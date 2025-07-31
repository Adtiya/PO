# Enterprise AI System

A comprehensive, production-ready enterprise AI system with advanced RBAC (Role-Based Access Control), microservices architecture, and AWS deployment capabilities.

## 🏗️ System Overview

This Enterprise AI System provides a complete foundation for building scalable AI applications with enterprise-grade security, authentication, and authorization. The system includes:

- **Advanced RBAC Framework**: Role-based access control with temporal and conditional permissions
- **JWT Authentication**: Secure token-based authentication system
- **Microservices Architecture**: Modular, scalable service design
- **AWS Production Ready**: Complete infrastructure-as-code for AWS deployment
- **PostgreSQL Database**: 15-table schema with comprehensive data models
- **RESTful APIs**: Well-documented API endpoints with OpenAPI/Swagger
- **Comprehensive Testing**: Full test suite for all components

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis (optional, for caching)
- Docker (for containerized deployment)
- AWS CLI (for AWS deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd enterprise_system
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database and other configuration
   ```

4. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb enterprise_ai_system
   
   # Run migrations
   cd migrations
   python run_migrations.py
   ```

5. **Start the backend server**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the system**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📁 Project Structure

```
enterprise_system/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API routes and endpoints
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── services/          # Business logic services
│   │   ├── db/                # Database configuration
│   │   └── main.py            # FastAPI application entry point
│   └── requirements.txt       # Python dependencies
├── microservices/             # Microservices components
│   ├── pi_service/           # Personal Intelligence service
│   ├── obr_service/          # Organizational Behavior Recognition
│   └── da_service/           # Data Analytics service
├── aws/                      # AWS deployment configurations
│   ├── docker/               # Docker configurations
│   ├── ecs/                  # ECS service definitions
│   ├── rds/                  # RDS database configurations
│   ├── iam/                  # IAM roles and policies
│   └── deploy.sh             # One-command deployment script
├── migrations/               # Database migrations
└── docs/                     # Documentation
```

## 🔐 Authentication & Authorization

### RBAC System Features

- **Role-Based Access Control**: Hierarchical role system with inheritance
- **Permission Management**: Granular permissions for resources and actions
- **Temporal Permissions**: Time-based access control
- **Conditional Permissions**: Context-aware authorization
- **JWT Tokens**: Secure, stateless authentication
- **User Management**: Complete user lifecycle management

### Default Roles

- **Admin**: Full system access
- **Manager**: Department-level management access
- **Analyst**: Data analysis and reporting access
- **User**: Basic user access

### API Authentication

All API endpoints require authentication via JWT tokens:

```bash
# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in subsequent requests
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🗄️ Database Schema

The system uses a comprehensive 15-table PostgreSQL schema:

### Core Tables
- **users**: User accounts and profiles
- **roles**: System roles and permissions
- **permissions**: Granular permission definitions
- **user_roles**: User-role assignments
- **role_permissions**: Role-permission mappings

### Advanced Features
- **temporal_permissions**: Time-based access control
- **conditional_permissions**: Context-aware permissions
- **audit_logs**: Comprehensive audit trail
- **conversations**: AI conversation management
- **documents**: Document management system

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout

### User Management
- `GET /api/v1/users/` - List users
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### RBAC Management
- `GET /api/v1/roles/` - List roles
- `POST /api/v1/roles/` - Create role
- `GET /api/v1/permissions/` - List permissions
- `POST /api/v1/permissions/` - Create permission

### Advanced Features
- `GET /api/v1/temporal-permissions/` - Temporal permissions
- `GET /api/v1/conditional-permissions/` - Conditional permissions
- `GET /api/v1/audit/` - Audit logs

## 🐳 Docker Deployment

### Local Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual services
docker build -t enterprise-ai-backend ./backend
docker run -p 8000:8000 enterprise-ai-backend
```

### Production Docker

```bash
# Build production image
docker build -f aws/docker/Dockerfile -t enterprise-ai-system .

# Run with production configuration
docker run -p 8000:8000 --env-file .env.production enterprise-ai-system
```

## ☁️ AWS Deployment

### One-Command Deployment

```bash
cd aws
./deploy.sh production us-east-1
```

### AWS Infrastructure

The system deploys to AWS with:

- **ECS Fargate**: Containerized application hosting
- **RDS PostgreSQL**: Managed database with Multi-AZ
- **ElastiCache Redis**: Caching and session management
- **Application Load Balancer**: Traffic distribution
- **CloudWatch**: Monitoring and logging
- **Secrets Manager**: Secure credential management
- **IAM**: Least-privilege security model

### Estimated AWS Costs

- **Development**: ~$50/month
- **Production**: ~$160/month
- **Enterprise**: ~$500/month (with high availability)

## 🧪 Testing

### Run Test Suite

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run specific test categories
pytest tests/test_auth.py
pytest tests/test_rbac.py
pytest tests/test_api.py
```

### RBAC Testing

```bash
# Run comprehensive RBAC test suite
python rbac_testing_suite.py

# Test specific RBAC features
python test_temporal_permissions.py
python test_conditional_permissions.py
```

## 📊 Monitoring & Observability

### Health Checks

- **Application Health**: `GET /health`
- **Database Health**: `GET /health/db`
- **Dependencies**: `GET /health/dependencies`

### Logging

The system provides comprehensive logging:

- **Application Logs**: Structured JSON logging
- **Audit Logs**: Complete audit trail in database
- **Security Logs**: Authentication and authorization events
- **Performance Logs**: Request timing and metrics

### Metrics

Key metrics tracked:

- Request latency and throughput
- Authentication success/failure rates
- Permission check performance
- Database query performance
- Error rates and types

## 🔒 Security Features

### Security Measures

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt with salt
- **SQL Injection Protection**: SQLAlchemy ORM
- **CORS Configuration**: Proper cross-origin handling
- **Rate Limiting**: API rate limiting (configurable)
- **Input Validation**: Pydantic model validation
- **Audit Logging**: Comprehensive audit trail

### Security Best Practices

- Environment-based configuration
- Secrets management via AWS Secrets Manager
- Least-privilege IAM roles
- Network security groups
- Encrypted data at rest and in transit
- Regular security updates

## 🚀 Production Considerations

### Scalability

- **Horizontal Scaling**: ECS auto-scaling based on metrics
- **Database Scaling**: RDS read replicas for read-heavy workloads
- **Caching**: Redis for session and data caching
- **Load Balancing**: Application Load Balancer with health checks

### High Availability

- **Multi-AZ Deployment**: Database and application redundancy
- **Auto-Recovery**: ECS service auto-recovery
- **Backup Strategy**: Automated RDS backups
- **Disaster Recovery**: Cross-region backup options

### Performance Optimization

- **Database Indexing**: Optimized database indexes
- **Connection Pooling**: Efficient database connections
- **Async Operations**: FastAPI async/await patterns
- **Caching Strategy**: Multi-level caching implementation

## 📚 Documentation

### API Documentation

- **Interactive Docs**: Available at `/docs` (Swagger UI)
- **OpenAPI Spec**: Available at `/openapi.json`
- **Redoc**: Available at `/redoc`

### Additional Documentation

- [Database Schema Design](docs/database_schema.md)
- [RBAC Implementation Guide](docs/rbac_guide.md)
- [AWS Deployment Guide](docs/aws_deployment.md)
- [API Reference](docs/api_reference.md)
- [Security Guide](docs/security.md)

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards

- **Python**: Follow PEP 8 style guide
- **Type Hints**: Use type hints for all functions
- **Documentation**: Document all public APIs
- **Testing**: Maintain >90% test coverage
- **Security**: Follow security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check the docs/ directory
- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub Discussions for questions

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running and accessible
2. **Authentication Errors**: Check JWT token expiration and format
3. **Permission Denied**: Verify user roles and permissions
4. **AWS Deployment**: Check IAM permissions and resource limits

## 🎯 Roadmap

### Upcoming Features

- [ ] GraphQL API support
- [ ] Real-time notifications via WebSocket
- [ ] Advanced analytics dashboard
- [ ] Machine learning model integration
- [ ] Multi-tenant support
- [ ] API versioning strategy
- [ ] Enhanced audit capabilities
- [ ] Performance optimization tools

### Version History

- **v1.0.0**: Initial release with core RBAC functionality
- **v1.1.0**: AWS deployment and microservices
- **v1.2.0**: Advanced permissions and audit logging
- **v2.0.0**: (Planned) GraphQL and real-time features

---

**Built with ❤️ for Enterprise AI Applications**

