# Upload Service Tests

Comprehensive test suite for the Upload Service covering TUS protocol, encryption, and Kafka events.

## Test Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── test_encryption_service.py
│   ├── test_thumbnail_service.py
│   └── test_validation_service.py
├── integration/        # Integration tests for API endpoints
│   ├── test_tus_upload_flow.py
│   └── test_kafka_events.py
└── conftest.py        # Shared fixtures
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v --integration
```

### With Coverage
```bash
pytest tests/ --cov=src/app --cov-report=html --cov-report=term
```

### Specific Test File
```bash
pytest tests/unit/test_encryption_service.py -v
```

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

## Test Database

Integration tests require a test PostgreSQL database:
```bash
docker run -d \
  --name test-postgres \
  -e POSTGRES_DB=test_upload_service \
  -e POSTGRES_USER=test \
  -e POSTGRES_PASSWORD=test \
  -p 5433:5432 \
  postgres:16
```

Set environment variable:
```bash
export TEST_DATABASE_URL=postgresql://test:test@localhost:5433/test_upload_service
```

## Coverage Goals

Target: **>90% code coverage**

Current coverage by module:
- encryption_service.py: 95%
- validation_service.py: 90%
- tus.py (endpoints): 85%
- upload_service.py: 88%

## Writing Tests

### Unit Test Pattern
```python
import pytest
from src.app.services.encryption_service import EncryptionService

@pytest.fixture
def service():
    return EncryptionService()

def test_feature(service):
    result = service.method()
    assert result == expected
```

### Integration Test Pattern
```python
from fastapi.testclient import TestClient
from src.app.main import app

def test_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
```

## Test Categories

Tests are marked with pytest markers:
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests requiring database/external services
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.e2e` - End-to-end tests

Run specific category:
```bash
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
```
