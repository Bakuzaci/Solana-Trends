# Testing Guide - Solana Trends

Quick reference for running tests in the Solana Trends project.

## Quick Start

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Test Status

✓ **Backend:** 17/17 tests passing (42% coverage)  
✓ **Frontend:** 9/9 tests passing  
✓ **Total:** 26/26 tests passing

## Backend Test Files

Located in `/backend/tests/`:

- `conftest.py` - Pytest fixtures (test database, test client)
- `test_api.py` - API endpoint tests (7 tests)
- `test_categorizer.py` - Token categorization tests (6 tests)
- `test_models.py` - Database model tests (4 tests)

### Backend Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::TestHealthEndpoints::test_root_endpoint -v
```

## Frontend Test Files

Located in `/frontend/src/`:

- `test/setup.js` - Vitest configuration
- `test/api.test.js` - API client tests (2 tests)
- `components/__tests__/AccelerationBar.test.jsx` - Component tests (4 tests)
- `components/__tests__/TimeWindowToggle.test.jsx` - Component tests (3 tests)

### Frontend Commands

```bash
# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

## Test Coverage

### Backend (42% overall)
- models.py: 94%
- schemas.py: 100%
- config.py: 100%
- categorizer.py: 67%
- main.py: 55%

### Coverage HTML Reports
- **Backend:** `/backend/htmlcov/index.html`
- **Frontend:** (run `npm run test:coverage`)

## Adding New Tests

### Backend Example
```python
# tests/test_new_feature.py
import pytest

async def test_new_endpoint(client):
    """Test description."""
    response = await client.get("/api/new-endpoint")
    assert response.status_code == 200
```

### Frontend Example
```javascript
// src/components/__tests__/NewComponent.test.jsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import NewComponent from '../NewComponent';

describe('NewComponent', () => {
  it('renders correctly', () => {
    render(<NewComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## Test Dependencies

### Backend
- pytest
- pytest-asyncio
- pytest-cov
- greenlet
- httpx (for test client)

### Frontend
- vitest
- @testing-library/react
- @testing-library/jest-dom
- @testing-library/user-event
- happy-dom

## CI/CD Integration

To add to CI pipeline:

```yaml
# .github/workflows/test.yml
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt pytest pytest-asyncio pytest-cov
          pytest tests/ -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run frontend tests
        run: |
          cd frontend
          npm install
          npm test
```

## See Also

- [TEST_REPORT.md](TEST_REPORT.md) - Detailed test report and coverage analysis
- [README.md](README.md) - Project overview and setup instructions
