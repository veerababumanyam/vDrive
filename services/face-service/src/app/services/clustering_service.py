"""Face clustering service using DBSCAN with cosine distance."""

from typing import Optional
from uuid import UUID, uuid4
import numpy as np

import structlog
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models import Face, FaceGroup, FaceEmbedding

logger = structlog.get_logger()


class ClusteringService:
    """
    Clusters face embeddings into groups using DBSCAN.

    Features:
    - Cosine distance metric for face similarity
    - Incremental clustering for new faces
    - Group merging and splitting
    """

    def __init__(self):
        self.eps = settings.DBSCAN_EPS
        self.min_samples = settings.DBSCAN_MIN_SAMPLES

    async def cluster_faces(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        force_recluster: bool = False,
    ) -> dict:
        """
        Cluster all faces in a workspace into groups.

        Args:
            db: Database session
            workspace_id: Workspace to cluster
            force_recluster: Re-cluster even if faces have groups

        Returns:
            Clustering statistics
        """
        try:
            # Get all faces with embeddings that need clustering
            query = (
                select(Face, FaceEmbedding)
                .join(FaceEmbedding, Face.embedding_id == FaceEmbedding.id)
                .where(Face.workspace_id == workspace_id)
            )

            if not force_recluster:
                query = query.where(Face.group_id.is_(None))

            result = await db.execute(query)
            rows = result.fetchall()

            if not rows:
                logger.info("No faces to cluster", workspace_id=str(workspace_id))
                return {"clustered": 0, "groups_created": 0}

            # Extract embeddings and face IDs
            face_ids = []
            embeddings = []

            for face, embedding in rows:
                face_ids.append(face.id)
                embeddings.append(np.array(embedding.embedding))

            embeddings_matrix = np.vstack(embeddings)

            # Compute cosine distance matrix
            distance_matrix = cosine_distances(embeddings_matrix)

            # Run DBSCAN clustering
            clustering = DBSCAN(
                eps=self.eps,
                min_samples=self.min_samples,
                metric="precomputed",
            ).fit(distance_matrix)

            labels = clustering.labels_

            # Process clusters
            groups_created = 0
            unique_labels = set(labels)

            for label in unique_labels:
                if label == -1:
                    # Noise points - each gets its own group
                    noise_indices = np.where(labels == label)[0]
                    for idx in noise_indices:
                        group = FaceGroup(
                            workspace_id=workspace_id,
                            face_count="1",
                        )
                        db.add(group)
                        await db.flush()

                        # Update face with group
                        face_id = face_ids[idx]
                        await db.execute(
                            update(Face)
                            .where(Face.id == face_id)
                            .values(group_id=group.id)
                        )
                        groups_created += 1
                else:
                    # Cluster members
                    cluster_indices = np.where(labels == label)[0]
                    cluster_face_ids = [face_ids[i] for i in cluster_indices]

                    # Create group
                    group = FaceGroup(
                        workspace_id=workspace_id,
                        face_count=str(len(cluster_face_ids)),
                    )
                    db.add(group)
                    await db.flush()

                    # Update all faces in cluster
                    await db.execute(
                        update(Face)
                        .where(Face.id.in_(cluster_face_ids))
                        .values(group_id=group.id)
                    )

                    # Set representative face (closest to centroid)
                    representative_id = await self._find_representative(
                        embeddings_matrix[cluster_indices],
                        cluster_face_ids,
                    )
                    group.representative_face_id = representative_id

                    groups_created += 1

            await db.commit()

            logger.info(
                "Face clustering complete",
                workspace_id=str(workspace_id),
                faces_clustered=len(face_ids),
                groups_created=groups_created,
            )

            return {
                "clustered": len(face_ids),
                "groups_created": groups_created,
            }

        except Exception as e:
            await db.rollback()
            logger.error("Clustering failed", error=str(e))
            raise

    async def assign_to_group(
        self,
        db: AsyncSession,
        face: Face,
        embedding: np.ndarray,
        workspace_id: UUID,
    ) -> Optional[UUID]:
        """
        Assign a single face to an existing group or create new one.

        This is used for incremental clustering when a new face is detected.

        Args:
            db: Database session
            face: The face to assign
            embedding: Face embedding
            workspace_id: Workspace ID

        Returns:
            Group ID assigned (existing or new)
        """
        try:
            # Find existing groups with similar faces
            from .embedding_service import embedding_service

            similar = await embedding_service.find_similar_faces(
                db=db,
                embedding=embedding,
                workspace_id=workspace_id,
                limit=5,
                threshold=1 - self.eps,  # Convert distance threshold to similarity
            )

            if similar and similar[0]["group_id"]:
                # Join existing group
                group_id = UUID(similar[0]["group_id"])

                # Update face
                face.group_id = group_id
                await db.flush()

                # Update group face count
                await db.execute(
                    update(FaceGroup)
                    .where(FaceGroup.id == group_id)
                    .values(
                        face_count=func.cast(
                            func.cast(FaceGroup.face_count, type_=int) + 1,
                            type_=str,
                        )
                    )
                )

                logger.debug(
                    "Face assigned to existing group",
                    face_id=str(face.id),
                    group_id=str(group_id),
                )

                return group_id
            else:
                # Create new group
                group = FaceGroup(
                    workspace_id=workspace_id,
                    representative_face_id=face.id,
                    face_count="1",
                )
                db.add(group)
                await db.flush()

                face.group_id = group.id

                logger.debug(
                    "New group created for face",
                    face_id=str(face.id),
                    group_id=str(group.id),
                )

                return group.id

        except Exception as e:
            logger.error("Group assignment failed", error=str(e))
            raise

    async def _find_representative(
        self,
        embeddings: np.ndarray,
        face_ids: list[UUID],
    ) -> UUID:
        """Find the most representative face (closest to centroid)."""
        if len(face_ids) == 1:
            return face_ids[0]

        # Compute centroid
        centroid = np.mean(embeddings, axis=0)

        # Find closest to centroid
        distances = np.linalg.norm(embeddings - centroid, axis=1)
        closest_idx = np.argmin(distances)

        return face_ids[closest_idx]

    async def merge_groups(
        self,
        db: AsyncSession,
        source_group_ids: list[UUID],
        target_group_id: UUID,
        workspace_id: UUID,
    ) -> dict:
        """
        Merge multiple groups into a target group.

        Args:
            db: Database session
            source_group_ids: Groups to merge from
            target_group_id: Group to merge into
            workspace_id: Workspace ID

        Returns:
            Merge statistics
        """
        try:
            # Verify all groups belong to workspace
            groups = await db.execute(
                select(FaceGroup)
                .where(FaceGroup.id.in_(source_group_ids + [target_group_id]))
                .where(FaceGroup.workspace_id == workspace_id)
            )
            found_groups = {g.id for g in groups.scalars()}

            if target_group_id not in found_groups:
                raise ValueError("Target group not found")

            # Move all faces from source groups to target
            faces_moved = 0
            for source_id in source_group_ids:
                if source_id == target_group_id:
                    continue

                result = await db.execute(
                    update(Face)
                    .where(Face.group_id == source_id)
                    .values(group_id=target_group_id)
                )
                faces_moved += result.rowcount

                # Delete source group
                await db.execute(
                    select(FaceGroup).where(FaceGroup.id == source_id)
                )

            # Update target group face count
            count_result = await db.execute(
                select(func.count(Face.id))
                .where(Face.group_id == target_group_id)
            )
            new_count = count_result.scalar()

            await db.execute(
                update(FaceGroup)
                .where(FaceGroup.id == target_group_id)
                .values(face_count=str(new_count))
            )

            await db.commit()

            logger.info(
                "Groups merged",
                source_groups=len(source_group_ids),
                target_group=str(target_group_id),
                faces_moved=faces_moved,
            )

            return {
                "merged": len(source_group_ids) - 1,
                "faces_moved": faces_moved,
                "target_group_id": str(target_group_id),
            }

        except Exception as e:
            await db.rollback()
            logger.error("Group merge failed", error=str(e))
            raise

    async def split_group(
        self,
        db: AsyncSession,
        group_id: UUID,
        face_ids: list[UUID],
        workspace_id: UUID,
    ) -> dict:
        """
        Split faces from a group into a new group.

        Args:
            db: Database session
            group_id: Group to split from
            face_ids: Face IDs to move to new group
            workspace_id: Workspace ID

        Returns:
            Split statistics with new group ID
        """
        try:
            # Verify group belongs to workspace
            group = await db.execute(
                select(FaceGroup)
                .where(FaceGroup.id == group_id)
                .where(FaceGroup.workspace_id == workspace_id)
            )
            original_group = group.scalar_one_or_none()

            if not original_group:
                raise ValueError("Group not found")

            # Create new group
            new_group = FaceGroup(
                workspace_id=workspace_id,
                face_count=str(len(face_ids)),
            )
            db.add(new_group)
            await db.flush()

            # Move specified faces to new group
            await db.execute(
                update(Face)
                .where(Face.id.in_(face_ids))
                .where(Face.group_id == group_id)
                .values(group_id=new_group.id)
            )

            # Update original group face count
            remaining_result = await db.execute(
                select(func.count(Face.id))
                .where(Face.group_id == group_id)
            )
            remaining_count = remaining_result.scalar()

            original_group.face_count = str(remaining_count)

            # Set representative for new group (first face)
            if face_ids:
                new_group.representative_face_id = face_ids[0]

            await db.commit()

            logger.info(
                "Group split",
                original_group=str(group_id),
                new_group=str(new_group.id),
                faces_moved=len(face_ids),
            )

            return {
                "new_group_id": str(new_group.id),
                "faces_moved": len(face_ids),
                "remaining_in_original": remaining_count,
            }

        except Exception as e:
            await db.rollback()
            logger.error("Group split failed", error=str(e))
            raise


# Global service instance
clustering_service = ClusteringService()
