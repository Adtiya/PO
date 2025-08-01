# Contributing to Enterprise AI System

Thank you for your interest in contributing to the Enterprise AI System! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information** including:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages and logs

### Suggesting Features

1. **Check the roadmap** to see if the feature is already planned
2. **Create a feature request** with detailed description
3. **Explain the use case** and benefits
4. **Consider implementation complexity** and breaking changes

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch** from `main`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Git
- Docker (optional)

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/enterprise-ai-system.git
   cd enterprise-ai-system
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

6. **Set up database**
   ```bash
   createdb enterprise_ai_system_dev
   cd migrations
   python run_migrations.py
   ```

7. **Run tests**
   ```bash
   pytest
   ```

## 📝 Coding Standards

### Python Code Style

We follow **PEP 8** with some modifications:

- **Line length**: 88 characters (Black formatter default)
- **Import sorting**: Use `isort`
- **Type hints**: Required for all public functions
- **Docstrings**: Google style docstrings

### Code Formatting

We use automated code formatting:

```bash
# Format code
black .
isort .

# Check formatting
black --check .
isort --check-only .
```

### Linting

We use multiple linters:

```bash
# Run all linters
flake8 .
mypy .
pylint backend/app/
```

### Example Code Style

```python
from typing import List, Optional
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[User]:
    """
    Retrieve a list of users from the database.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: Whether to return only active users
        
    Returns:
        List of user objects
        
    Raises:
        HTTPException: If database query fails
    """
    try:
        query = select(User)
        if active_only:
            query = query.where(User.is_active == True)
        
        result = await db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve users: {str(e)}"
        )
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── fixtures/      # Test fixtures and data
```

### Writing Tests

1. **Use pytest** for all tests
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use descriptive test names**
4. **Mock external dependencies**
5. **Test both success and failure cases**

### Test Example

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import AuthService


class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test successful user authentication."""
        # Arrange
        auth_service = AuthService(db_session)
        email = test_user.email
        password = "test_password"
        
        # Act
        result = await auth_service.authenticate_user(email, password)
        
        # Assert
        assert result is not None
        assert result.email == email
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test authentication with invalid password."""
        # Arrange
        auth_service = AuthService(db_session)
        email = test_user.email
        password = "wrong_password"
        
        # Act
        result = await auth_service.authenticate_user(email, password)
        
        # Assert
        assert result is None
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Run tests in parallel
pytest -n auto
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: All public functions must have docstrings
- **Type hints**: Use type hints for better code clarity
- **Comments**: Explain complex logic, not obvious code
- **README updates**: Update README for new features

### API Documentation

- **OpenAPI/Swagger**: Automatically generated from FastAPI
- **Endpoint descriptions**: Clear, concise descriptions
- **Request/response examples**: Provide realistic examples
- **Error codes**: Document all possible error responses

### Documentation Example

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate


router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    active_only: bool = Query(True, description="Filter for active users only"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[UserResponse]:
    """
    Retrieve a list of users.
    
    This endpoint returns a paginated list of users. Only authenticated users
    with the 'users.read' permission can access this endpoint.
    
    - **skip**: Number of users to skip (for pagination)
    - **limit**: Maximum number of users to return (1-1000)
    - **active_only**: Whether to return only active users
    
    Returns a list of user objects with basic information.
    """
    # Implementation here
    pass
```

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure tests pass**: `pytest`
2. **Check code style**: `black --check . && isort --check-only .`
3. **Run linters**: `flake8 . && mypy .`
4. **Update documentation**: If adding new features
5. **Add changelog entry**: For user-facing changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] All tests pass
```

### Review Process

1. **Automated checks** must pass
2. **At least one reviewer** approval required
3. **Address feedback** promptly
4. **Squash commits** before merging (if requested)

## 🏷️ Versioning

We use **Semantic Versioning** (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Process

1. **Update version** in `__init__.py`
2. **Update CHANGELOG.md**
3. **Create release tag**
4. **Deploy to staging** for testing
5. **Deploy to production** after approval

## 🐛 Debugging

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL is running
   - Verify connection string in `.env`
   - Ensure database exists

2. **Import errors**
   - Check virtual environment is activated
   - Verify all dependencies are installed
   - Check Python path configuration

3. **Test failures**
   - Run tests individually to isolate issues
   - Check test database configuration
   - Verify test fixtures are properly set up

### Debugging Tools

- **pdb**: Python debugger
- **pytest --pdb**: Drop into debugger on test failure
- **logging**: Use structured logging for debugging
- **FastAPI debug mode**: Enable for detailed error messages

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Code Reviews**: Pull request discussions

### Resources

- **Documentation**: Check the `docs/` directory
- **Examples**: Look at existing code for patterns
- **Tests**: Existing tests show expected behavior
- **Architecture**: Review system architecture documents

## 🎯 Development Workflow

### Git Workflow

1. **Create feature branch** from `main`
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** and commit regularly
   ```bash
   git add .
   git commit -m "feat: add user authentication endpoint"
   ```

3. **Push branch** and create pull request
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

We follow **Conventional Commits**:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Examples:
```
feat(auth): add JWT token refresh endpoint
fix(rbac): resolve permission checking bug
docs: update API documentation
test(auth): add integration tests for login flow
```

## 🏆 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributors** page

Thank you for contributing to the Enterprise AI System! 🚀

