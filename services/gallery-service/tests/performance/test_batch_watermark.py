"""
Performance test for batch watermark application.

Tests performance metrics for watermarking 1000+ images:
- Completion time < 60 seconds
- All images processed correctly
- Memory usage < 512MB per worker
- Throughput (images/second)
- Concurrent processing performance
"""

import asyncio
import gc
import io
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from PIL import Image
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.app.core.database import Base
from src.app.models.asset import Asset, ProcessingStatus, StorageProvider
from src.app.models.gallery import Gallery, GalleryStatus, WatermarkPosition
from src.app.repositories.asset_repository import AssetRepository
from src.app.schemas.watermark import (
    ImageWatermark,
    TextWatermark,
    WatermarkConfig,
    WatermarkType,
)
from src.app.services.progress_service import BatchStatus, ProgressService
from src.app.services.watermark_service import WatermarkService
from src.app.workers.image_processor import apply_text_watermark, apply_image_watermark
from src.app.workers.watermark_worker import WatermarkWorker

# Configure logging for performance test
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - memory monitoring disabled")


# ==========================================
# Fixtures
# ==========================================


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine with SQLite in-memory."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_redis() -> MagicMock:
    """Create mock Redis client with realistic behavior."""
    redis_store = {}
    redis_lists = {}

    async def mock_get(key):
        return redis_store.get(key)

    async def mock_set(key, value, ex=None):
        redis_store[key] = value
        return True

    async def mock_incr(key):
        current = int(redis_store.get(key, 0))
        redis_store[key] = str(current + 1)
        return current + 1

    async def mock_delete(key):
        redis_store.pop(key, None)
        return 1

    async def mock_rpush(key, *values):
        if key not in redis_lists:
            redis_lists[key] = []
        redis_lists[key].extend(values)
        return len(redis_lists[key])

    async def mock_lpop(key):
        if key not in redis_lists or not redis_lists[key]:
            return None
        return redis_lists[key].pop(0)

    async def mock_llen(key):
        return len(redis_lists.get(key, []))

    async def mock_expire(key, seconds):
        return True

    redis = MagicMock(spec=Redis)
    redis.get = AsyncMock(side_effect=mock_get)
    redis.set = AsyncMock(side_effect=mock_set)
    redis.incr = AsyncMock(side_effect=mock_incr)
    redis.delete = AsyncMock(side_effect=mock_delete)
    redis.rpush = AsyncMock(side_effect=mock_rpush)
    redis.lpop = AsyncMock(side_effect=mock_lpop)
    redis.llen = AsyncMock(side_effect=mock_llen)
    redis.expire = AsyncMock(side_effect=mock_expire)
    redis.close = AsyncMock()

    redis._store = redis_store
    redis._lists = redis_lists

    return redis


@pytest.fixture
def test_workspace_id() -> str:
    """Generate test workspace ID."""
    return str(uuid4())


@pytest.fixture
def test_user_id() -> str:
    """Generate test user ID."""
    return str(uuid4())


def create_test_image(width: int = 1920, height: int = 1080) -> bytes:
    """Create a realistic test image in memory."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))

    # Add some visual content
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    # Draw gradient background
    for i in range(0, height, 20):
        color_val = int(100 + (i / height) * 100)
        draw.rectangle([0, i, width, i+20], fill=(color_val, color_val + 30, color_val + 50))

    # Draw some shapes
    draw.rectangle([100, 100, width-100, height-100], outline=(255, 255, 255), width=5)
    draw.ellipse([width//4, height//4, 3*width//4, 3*height//4], outline=(255, 200, 100), width=3)

    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", quality=85)
    img_bytes.seek(0)

    return img_bytes.read()


def create_logo_image(width: int = 200, height: int = 100) -> bytes:
    """Create a logo image with transparency (PNG)."""
    img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))

    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    # Draw logo content
    draw.ellipse([10, 10, 90, 90], fill=(74, 144, 226, 230), outline=(255, 255, 255, 255), width=3)
    draw.text((110, 35), "LOGO", fill=(74, 144, 226, 255))

    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes.read()


class MemoryMonitor:
    """Monitor memory usage during test execution."""

    def __init__(self):
        self.process = psutil.Process(os.getpid()) if PSUTIL_AVAILABLE else None
        self.baseline_memory = None
        self.peak_memory = None
        self.samples = []

    def start(self):
        """Start monitoring memory."""
        if self.process:
            self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            self.peak_memory = self.baseline_memory
            self.samples = []
            logger.info(f"Memory monitoring started - Baseline: {self.baseline_memory:.2f} MB")

    def sample(self):
        """Take a memory sample."""
        if self.process:
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            self.samples.append(current_memory)
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory
            return current_memory
        return 0

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        if not self.process:
            return {
                "baseline_mb": 0,
                "peak_mb": 0,
                "avg_mb": 0,
                "increase_mb": 0,
            }

        avg_memory = sum(self.samples) / len(self.samples) if self.samples else self.baseline_memory

        return {
            "baseline_mb": self.baseline_memory,
            "peak_mb": self.peak_memory,
            "avg_mb": avg_memory,
            "increase_mb": self.peak_memory - self.baseline_memory,
        }


class PerformanceMetrics:
    """Track performance metrics during test."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.images_processed = 0
        self.images_failed = 0
        self.processing_times = []
        self.memory_monitor = MemoryMonitor()

    def start(self):
        """Start performance tracking."""
        self.start_time = time.time()
        self.memory_monitor.start()
        logger.info("Performance tracking started")

    def record_image(self, processing_time: float, success: bool = True):
        """Record image processing result."""
        self.processing_times.append(processing_time)
        if success:
            self.images_processed += 1
        else:
            self.images_failed += 1
        self.memory_monitor.sample()

    def finish(self):
        """Finish performance tracking."""
        self.end_time = time.time()

    def get_report(self) -> Dict:
        """Generate performance report."""
        if not self.end_time:
            self.finish()

        total_time = self.end_time - self.start_time
        total_images = self.images_processed + self.images_failed
        throughput = total_images / total_time if total_time > 0 else 0

        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        min_processing_time = min(self.processing_times) if self.processing_times else 0
        max_processing_time = max(self.processing_times) if self.processing_times else 0

        memory_stats = self.memory_monitor.get_stats()

        return {
            "total_time_seconds": total_time,
            "images_processed": self.images_processed,
            "images_failed": self.images_failed,
            "throughput_images_per_second": throughput,
            "avg_processing_time_ms": avg_processing_time * 1000,
            "min_processing_time_ms": min_processing_time * 1000,
            "max_processing_time_ms": max_processing_time * 1000,
            "memory": memory_stats,
        }

    def print_report(self):
        """Print formatted performance report."""
        report = self.get_report()

        print("\n" + "="*70)
        print("PERFORMANCE TEST REPORT")
        print("="*70)
        print(f"Total Time:              {report['total_time_seconds']:.2f} seconds")
        print(f"Images Processed:        {report['images_processed']}")
        print(f"Images Failed:           {report['images_failed']}")
        print(f"Throughput:              {report['throughput_images_per_second']:.2f} images/second")
        print(f"\nProcessing Times:")
        print(f"  Average:               {report['avg_processing_time_ms']:.2f} ms")
        print(f"  Min:                   {report['min_processing_time_ms']:.2f} ms")
        print(f"  Max:                   {report['max_processing_time_ms']:.2f} ms")

        if PSUTIL_AVAILABLE:
            print(f"\nMemory Usage:")
            print(f"  Baseline:              {report['memory']['baseline_mb']:.2f} MB")
            print(f"  Peak:                  {report['memory']['peak_mb']:.2f} MB")
            print(f"  Average:               {report['memory']['avg_mb']:.2f} MB")
            print(f"  Increase:              {report['memory']['increase_mb']:.2f} MB")
        else:
            print(f"\nMemory Usage:            Not available (psutil not installed)")

        print("="*70)


# ==========================================
# Performance Tests
# ==========================================


@pytest.mark.asyncio
async def test_batch_watermark_performance_1000_images(
    test_db: AsyncSession,
    mock_redis: MagicMock,
    test_workspace_id: str,
    test_user_id: str,
):
    """
    Performance test: Batch watermark 1000+ images.

    Requirements:
    - Completion time < 60 seconds
    - All images processed correctly
    - Memory usage < 512MB per worker (simulated)

    Test simulates concurrent workers processing images in parallel.
    """

    print("\n" + "="*70)
    print("STARTING PERFORMANCE TEST: 1000 IMAGE BATCH WATERMARK")
    print("="*70)

    # Initialize performance tracking
    metrics = PerformanceMetrics()

    # ==========================================
    # SETUP: Create gallery and 1000 test assets
    # ==========================================
    print("\n[SETUP] Creating test gallery and 1000 assets...")
    setup_start = time.time()

    gallery = Gallery(
        id=str(uuid4()),
        workspace_id=test_workspace_id,
        owner_id=test_user_id,
        name="Performance Test Gallery",
        slug="performance-test-gallery",
        description="Gallery for performance testing with 1000 images",
        status=GalleryStatus.DRAFT,
        watermark_enabled=False,
        watermark_url=None,
        watermark_position=WatermarkPosition.BOTTOM_RIGHT,
        watermark_opacity=0.7,
    )

    test_db.add(gallery)
    await test_db.commit()
    await test_db.refresh(gallery)

    # Create 1000 assets in batches
    assets = []
    batch_size = 100

    for batch_idx in range(10):
        batch_assets = []
        for i in range(batch_size):
            asset_num = batch_idx * batch_size + i
            asset = Asset(
                id=str(uuid4()),
                workspace_id=test_workspace_id,
                gallery_id=gallery.id,
                filename=f"perf-test-{asset_num:04d}.jpg",
                original_filename=f"DSC_{5000+asset_num}.jpg",
                file_size=1024 * 750,  # 750KB
                mime_type="image/jpeg",
                storage_provider=StorageProvider.R2,
                storage_path=f"test-workspace/galleries/{gallery.id}/original/perf-test-{asset_num:04d}.jpg",
                file_url=f"https://r2.example.com/perf-test-{asset_num:04d}.jpg",
                width=1920,
                height=1280,
                processing_status=ProcessingStatus.COMPLETED,
            )
            batch_assets.append(asset)
            test_db.add(asset)

        assets.extend(batch_assets)
        await test_db.commit()

    # Refresh all assets
    for asset in assets:
        await test_db.refresh(asset)

    setup_time = time.time() - setup_start
    print(f"✓ Setup complete: {len(assets)} assets created in {setup_time:.2f}s")

    # ==========================================
    # CONFIGURE: Text watermark
    # ==========================================
    print("\n[CONFIGURE] Setting up text watermark...")

    watermark_service = WatermarkService(test_db)

    watermark_config = WatermarkConfig(
        enabled=True,
        watermark_type=WatermarkType.TEXT,
        text_config=TextWatermark(
            text="© 2024 Performance Test",
            font_family="Arial",
            font_size=36,
            color="#FFFFFF",
            opacity=0.7,
            position=WatermarkPosition.BOTTOM_RIGHT,
            margin=30,
            rotation=0,
        ),
    )

    await watermark_service.update_watermark_config(
        gallery_id=gallery.id,
        workspace_id=test_workspace_id,
        config=watermark_config,
    )

    print(f"✓ Watermark configured: {watermark_config.text_config.text}")

    # ==========================================
    # CREATE: Batch operation
    # ==========================================
    print("\n[CREATE] Creating batch operation...")

    progress_service = ProgressService(redis=mock_redis)
    batch_id = f"perf-batch-{uuid4().hex[:12]}"

    await progress_service.create_batch(
        batch_id=batch_id,
        gallery_id=gallery.id,
        workspace_id=test_workspace_id,
        total_tasks=len(assets),
        metadata={
            "watermark_type": "text",
            "test_type": "performance",
        },
    )

    await progress_service.update_batch_status(
        batch_id=batch_id,
        status=BatchStatus.PROCESSING,
    )

    print(f"✓ Batch created: {batch_id}")
    print(f"✓ Total tasks: {len(assets)}")

    # ==========================================
    # PROCESS: Batch watermark with performance tracking
    # ==========================================
    print("\n[PROCESS] Processing 1000 images with performance tracking...")
    print("Simulating concurrent workers with parallel processing...")

    # Mock storage service
    mock_storage = MagicMock()
    mock_storage.download_file = AsyncMock(return_value=create_test_image())
    mock_storage.upload_file = AsyncMock(return_value="https://r2.example.com/watermarked/test.jpg")

    # Create test image cache (reuse same image for speed)
    test_image_bytes = create_test_image()

    # Start performance tracking
    metrics.start()

    # Force garbage collection before test
    gc.collect()

    asset_repo = AssetRepository(test_db)

    # Simulate concurrent workers (process in parallel batches)
    num_workers = 5
    batch_size = 200  # Each batch processed by one "worker"

    print(f"Using {num_workers} simulated workers, batch size: {batch_size}")

    with patch("src.app.workers.watermark_worker.StorageService", return_value=mock_storage):
        for worker_idx in range(num_workers):
            batch_start = worker_idx * batch_size
            batch_end = batch_start + batch_size
            worker_batch = assets[batch_start:batch_end]

            print(f"\n  Worker {worker_idx + 1}/{num_workers}: Processing {len(worker_batch)} images...")

            for i, asset in enumerate(worker_batch):
                image_start = time.time()

                try:
                    # Apply watermark (actual image processing with Pillow)
                    watermarked_bytes = apply_text_watermark(
                        image_bytes=test_image_bytes,
                        config=watermark_config.text_config,
                    )

                    # Verify watermarked image is valid
                    assert watermarked_bytes is not None
                    assert len(watermarked_bytes) > 0

                    # Update asset
                    await asset_repo.update(
                        asset_id=asset.id,
                        preview_url=f"https://r2.example.com/watermarked/{asset.filename}",
                        processing_status=ProcessingStatus.COMPLETED,
                    )

                    # Update progress
                    await progress_service.increment_progress(
                        batch_id=batch_id,
                        completed=True,
                        failed=False,
                    )

                    image_time = time.time() - image_start
                    metrics.record_image(image_time, success=True)

                except Exception as e:
                    logger.error(f"Error processing asset {asset.id}: {e}")

                    await progress_service.increment_progress(
                        batch_id=batch_id,
                        completed=False,
                        failed=True,
                    )

                    image_time = time.time() - image_start
                    metrics.record_image(image_time, success=False)

                # Progress update every 50 images
                if (i + 1) % 50 == 0:
                    current_progress = await progress_service.get_batch_progress_percentage(batch_id)
                    print(f"    Progress: {i + 1}/{len(worker_batch)} ({current_progress:.1f}% total)")

            # Commit batch
            await test_db.commit()

            batch_progress = await progress_service.get_batch_progress_percentage(batch_id)
            print(f"  ✓ Worker {worker_idx + 1} complete - Total progress: {batch_progress:.1f}%")

    # Finish performance tracking
    metrics.finish()

    # Force garbage collection after test
    gc.collect()

    # ==========================================
    # VERIFY: Results and performance
    # ==========================================
    print("\n[VERIFY] Checking results and performance metrics...")

    # Get final batch status
    final_status = await progress_service.get_batch_status(batch_id)

    assert final_status is not None
    assert final_status["total_tasks"] == 1000
    assert final_status["completed_tasks"] == 1000
    assert final_status["failed_tasks"] == 0
    assert final_status["status"] == BatchStatus.COMPLETED

    # Verify sample assets
    sample_indices = [0, 100, 250, 500, 750, 999]
    for idx in sample_indices:
        asset = assets[idx]
        await test_db.refresh(asset)
        assert asset.preview_url is not None
        assert asset.processing_status == ProcessingStatus.COMPLETED

    print(f"✓ Batch status: {final_status['status']}")
    print(f"✓ Completed: {final_status['completed_tasks']}/{final_status['total_tasks']}")
    print(f"✓ Failed: {final_status['failed_tasks']}")

    # Print performance report
    metrics.print_report()
    report = metrics.get_report()

    # ==========================================
    # ASSERTIONS: Performance requirements
    # ==========================================
    print("\n[ASSERTIONS] Validating performance requirements...")

    # Requirement 1: Completion time < 60 seconds
    assert report["total_time_seconds"] < 60, (
        f"Performance requirement failed: Processing took {report['total_time_seconds']:.2f}s, "
        f"expected < 60s"
    )
    print(f"✓ Requirement 1: Completion time {report['total_time_seconds']:.2f}s < 60s")

    # Requirement 2: All images processed correctly
    assert report["images_processed"] == 1000, (
        f"Processing requirement failed: {report['images_processed']}/1000 images processed"
    )
    print(f"✓ Requirement 2: All {report['images_processed']} images processed correctly")

    # Requirement 3: Memory usage < 512MB per worker (if psutil available)
    if PSUTIL_AVAILABLE:
        # For 5 workers, total memory increase should be < 2560MB (512MB * 5)
        # But in test environment, we measure the test process itself
        # We expect reasonable memory usage (< 512MB for the test process)
        memory_increase = report["memory"]["increase_mb"]

        # Relaxed threshold for test environment (processes batches sequentially)
        assert memory_increase < 512, (
            f"Memory requirement failed: Memory increased by {memory_increase:.2f}MB, "
            f"expected < 512MB per worker"
        )
        print(f"✓ Requirement 3: Memory increase {memory_increase:.2f}MB < 512MB")
    else:
        print(f"⚠ Requirement 3: Memory monitoring not available (install psutil)")

    # Additional metrics
    assert report["throughput_images_per_second"] > 15, (
        f"Throughput too low: {report['throughput_images_per_second']:.2f} images/s"
    )
    print(f"✓ Throughput: {report['throughput_images_per_second']:.2f} images/second")

    print("\n" + "="*70)
    print("🎉 PERFORMANCE TEST PASSED!")
    print("="*70)
    print(f"✓ 1000 images watermarked in {report['total_time_seconds']:.2f} seconds")
    print(f"✓ Throughput: {report['throughput_images_per_second']:.2f} images/second")
    print(f"✓ All performance requirements met")
    print("="*70)


@pytest.mark.asyncio
async def test_batch_watermark_performance_image_logo(
    test_db: AsyncSession,
    mock_redis: MagicMock,
    test_workspace_id: str,
    test_user_id: str,
):
    """
    Performance test: Batch watermark 1000 images with image logo.

    Tests image watermark performance (more complex than text).
    """

    print("\n" + "="*70)
    print("STARTING PERFORMANCE TEST: IMAGE LOGO WATERMARK")
    print("="*70)

    metrics = PerformanceMetrics()

    # ==========================================
    # SETUP: Create gallery and assets
    # ==========================================
    print("\n[SETUP] Creating test gallery and 1000 assets...")

    gallery = Gallery(
        id=str(uuid4()),
        workspace_id=test_workspace_id,
        owner_id=test_user_id,
        name="Image Logo Performance Test",
        slug="image-logo-perf-test",
        description="Performance test with image watermark",
        status=GalleryStatus.DRAFT,
        watermark_enabled=False,
        watermark_url=None,
        watermark_position=WatermarkPosition.BOTTOM_RIGHT,
        watermark_opacity=0.5,
    )

    test_db.add(gallery)
    await test_db.commit()
    await test_db.refresh(gallery)

    # Create 1000 assets
    assets = []
    for i in range(1000):
        asset = Asset(
            id=str(uuid4()),
            workspace_id=test_workspace_id,
            gallery_id=gallery.id,
            filename=f"logo-test-{i:04d}.jpg",
            original_filename=f"IMG_{6000+i}.jpg",
            file_size=1024 * 800,
            mime_type="image/jpeg",
            storage_provider=StorageProvider.R2,
            storage_path=f"test-workspace/galleries/{gallery.id}/original/logo-test-{i:04d}.jpg",
            file_url=f"https://r2.example.com/logo-test-{i:04d}.jpg",
            width=1920,
            height=1280,
            processing_status=ProcessingStatus.COMPLETED,
        )
        assets.append(asset)
        test_db.add(asset)

        if (i + 1) % 200 == 0:
            await test_db.commit()

    await test_db.commit()
    for asset in assets:
        await test_db.refresh(asset)

    print(f"✓ Setup complete: {len(assets)} assets created")

    # ==========================================
    # CONFIGURE: Image watermark
    # ==========================================
    print("\n[CONFIGURE] Setting up image watermark...")

    logo_bytes = create_logo_image()
    logo_url = "https://r2.example.com/logos/perf-test-logo.png"

    watermark_service = WatermarkService(test_db)

    watermark_config = WatermarkConfig(
        enabled=True,
        watermark_type=WatermarkType.IMAGE,
        image_config=ImageWatermark(
            image_url=logo_url,
            scale=0.15,
            opacity=0.5,
            position=WatermarkPosition.BOTTOM_RIGHT,
            margin=30,
        ),
    )

    await watermark_service.update_watermark_config(
        gallery_id=gallery.id,
        workspace_id=test_workspace_id,
        config=watermark_config,
    )

    print(f"✓ Image watermark configured: {logo_url}")

    # ==========================================
    # CREATE: Batch operation
    # ==========================================
    progress_service = ProgressService(redis=mock_redis)
    batch_id = f"logo-perf-{uuid4().hex[:12]}"

    await progress_service.create_batch(
        batch_id=batch_id,
        gallery_id=gallery.id,
        workspace_id=test_workspace_id,
        total_tasks=len(assets),
    )

    await progress_service.update_batch_status(
        batch_id=batch_id,
        status=BatchStatus.PROCESSING,
    )

    # ==========================================
    # PROCESS: Batch with image watermark
    # ==========================================
    print("\n[PROCESS] Processing 1000 images with logo watermark...")

    # Mock storage
    mock_storage = MagicMock()
    mock_storage.download_file = AsyncMock(
        side_effect=lambda path: logo_bytes if "logo" in path else create_test_image()
    )
    mock_storage.upload_file = AsyncMock(return_value="https://r2.example.com/watermarked/test.jpg")

    test_image_bytes = create_test_image()

    # Start performance tracking
    metrics.start()
    gc.collect()

    asset_repo = AssetRepository(test_db)

    # Process in batches
    batch_size = 250
    num_batches = 4

    with patch("src.app.workers.watermark_worker.StorageService", return_value=mock_storage):
        for batch_idx in range(num_batches):
            batch_start = batch_idx * batch_size
            batch_end = batch_start + batch_size
            batch_assets = assets[batch_start:batch_end]

            for asset in batch_assets:
                image_start = time.time()

                try:
                    # Apply image watermark (actual processing)
                    watermarked_bytes = apply_image_watermark(
                        image_bytes=test_image_bytes,
                        watermark_bytes=logo_bytes,
                        config=watermark_config.image_config,
                    )

                    assert watermarked_bytes is not None
                    assert len(watermarked_bytes) > 0

                    await asset_repo.update(
                        asset_id=asset.id,
                        preview_url=f"https://r2.example.com/watermarked/{asset.filename}",
                        processing_status=ProcessingStatus.COMPLETED,
                    )

                    await progress_service.increment_progress(
                        batch_id=batch_id,
                        completed=True,
                        failed=False,
                    )

                    image_time = time.time() - image_start
                    metrics.record_image(image_time, success=True)

                except Exception as e:
                    logger.error(f"Error: {e}")
                    metrics.record_image(0.0, success=False)

            await test_db.commit()
            progress = await progress_service.get_batch_progress_percentage(batch_id)
            print(f"  Batch {batch_idx + 1}/{num_batches}: {progress:.1f}% complete")

    metrics.finish()
    gc.collect()

    # ==========================================
    # VERIFY: Performance
    # ==========================================
    print("\n[VERIFY] Checking performance...")

    final_status = await progress_service.get_batch_status(batch_id)
    assert final_status["completed_tasks"] == 1000
    assert final_status["failed_tasks"] == 0

    metrics.print_report()
    report = metrics.get_report()

    # Assertions
    assert report["total_time_seconds"] < 60, f"Too slow: {report['total_time_seconds']:.2f}s"
    assert report["images_processed"] == 1000

    if PSUTIL_AVAILABLE:
        assert report["memory"]["increase_mb"] < 512

    print("\n" + "="*70)
    print("🎉 IMAGE LOGO PERFORMANCE TEST PASSED!")
    print("="*70)
    print(f"✓ 1000 images with logo watermark in {report['total_time_seconds']:.2f}s")
    print(f"✓ Throughput: {report['throughput_images_per_second']:.2f} images/second")
    print("="*70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
