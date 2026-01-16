# Specification: Phase 4 - AI & Gallery Services

**Version**: 1.0
**Status**: In Progress
**Branch**: 007-ai-gallery-services

## Overview

This specification covers the implementation of AI-powered features for the RawDrive photography platform, including face detection, semantic search, RAG-based chat, and real-time gallery updates.

## Goals

1. Enable photographers to find photos of specific people using face detection
2. Allow natural language search across photo libraries
3. Provide AI-powered insights through conversational interface
4. Real-time gallery updates via WebSocket connections
5. Intelligent caption suggestions for photos

## New Services

### Face Service (Port 8002)
- Face detection using Google Cloud Vision API
- Face embedding generation using DeepFace/ArcFace (512-dim vectors)
- Face clustering using DBSCAN with cosine distance
- People group management (merge, split, name)
- "Find Me" selfie matching feature

### AI Search Service (Port 8009)
- Semantic search using CLIP ViT-L/14 (1536-dim embeddings)
- pgvector for vector similarity search
- RAG conversations using Gemini 2.5 Flash
- Intelligent caption generation

### Gallery Service Enhancements (Port 8004)
- WebSocket real-time updates
- Preview mode for galleries
- Batch operations (download, move, delete)

## User Stories

### US1 - Find Photos of a Specific Person (P1)
**As a** photographer
**I want to** automatically detect and group photos by people
**So that I can** quickly find all photos of a specific client

**Acceptance Criteria:**
- System detects faces in uploaded photos automatically
- Faces are grouped by person using embedding similarity
- Users can search for photos by selecting a person
- "Find Me" feature allows selfie-based search

### US2 - Search Photos Using Natural Language (P1)
**As a** photographer
**I want to** search my photo library using natural language
**So that I can** find photos without manual tagging

**Acceptance Criteria:**
- Photos are automatically embedded using CLIP
- Natural language queries return relevant results
- Similar photo suggestions based on image similarity

### US3 - Ask Questions About My Photos (P2)
**As a** photographer
**I want to** ask questions about my photo library
**So that I can** get insights and recommendations

**Acceptance Criteria:**
- RAG-based chat interface
- Context-aware responses using photo metadata
- Conversation history maintained

### US4 - View Public Gallery (P1)
**As a** client
**I want to** view shared galleries with real-time updates
**So that I can** see new photos as they're added

**Acceptance Criteria:**
- WebSocket connection for real-time updates
- Magic link authentication
- Photo added/removed notifications

### US5 - Receive Intelligent Caption Suggestions (P2)
**As a** photographer
**I want to** get AI-generated caption suggestions
**So that I can** improve SEO and client delivery

**Acceptance Criteria:**
- Context-aware captions (wedding, portrait, etc.)
- Multiple style suggestions
- Regeneration support

### US6 - Manage People Groups (P2)
**As a** photographer
**I want to** manage and merge people groups
**So that I can** correct misidentified faces

**Acceptance Criteria:**
- Merge duplicate groups
- Split incorrectly merged groups
- Name people groups

### US7 - Preview Client Gallery (P2)
**As a** photographer
**I want to** preview how clients see galleries
**So that I can** ensure quality before publishing

**Acceptance Criteria:**
- Preview mode toggle
- Client view simulation

### US8 - Batch Operations on Gallery Photos (P3)
**As a** photographer
**I want to** perform batch operations
**So that I can** efficiently manage large galleries

**Acceptance Criteria:**
- Batch download with ZIP
- Batch move between galleries
- Batch delete with confirmation
- Progress notifications via WebSocket

## Technical Requirements

### Database
- PostgreSQL 16 with pgvector extension
- Face embeddings: Vector(512) with IVFFlat index
- Photo embeddings: Vector(1536) with HNSW index

### Message Queue
- Kafka topics: face.detected, asset.embedding.generated
- Consumers for asset.processed events

### AI Services
- Google Cloud Vision API for face detection
- DeepFace/ArcFace for face embeddings
- CLIP ViT-L/14 for photo embeddings
- Gemini 2.5 Flash for RAG and captions

### Caching
- Redis for face group caching
- Redis Pub/Sub for WebSocket scaling

## Non-Functional Requirements

- Face detection latency < 2s per image
- Semantic search latency < 500ms
- WebSocket connection stability
- Multi-tenancy isolation (workspace_id)
- KEDA autoscaling for GPU workloads
