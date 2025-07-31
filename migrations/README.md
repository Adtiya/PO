# Database Migrations

This directory contains PostgreSQL database migrations for the Enterprise AI System. The migrations implement a comprehensive schema with dynamic RBAC, analytics, security, and audit capabilities.

## Migration Files

1. **001_initial_schema.sql** - Core identity and authorization tables
2. **002_sso_and_llm_domain.sql** - SSO integration and LLM domain tables  
3. **003_analytics_security_audit.sql** - Analytics, security, and audit tables
4. **004_seed_data.sql** - Default data and configuration

## Prerequisites

- PostgreSQL 12+ with required extensions
- Python 3.8+ with psycopg2 package
- Database connection with CREATE privileges

## Required PostgreSQL Extensions

The migrations require these PostgreSQL extensions:
- `uuid-ossp` - UUID generation functions
- `pgcrypto` - Cryptographic functions

## Quick Start

### 1. Install Dependencies

```bash
pip install psycopg2-binary
```

### 2. Set Database URL

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/enterprise_ai"
```

### 3. Run Migrations

```bash
# Make migration runner executable
chmod +x run_migrations.py

# Run all pending migrations
./run_migrations.py migrate

# Check migration status
./run_migrations.py status
```

## Migration Runner Commands

### Run Migrations

```bash
# Run all pending migrations
./run_migrations.py migrate

# Run migrations up to a specific file
./run_migrations.py migrate --target 002_sso_and_llm_domain.sql

# Specify custom database URL
./run_migrations.py migrate --database-url "postgresql://user:pass@host:port/db"
```

### Check Status

```bash
# Show which migrations have been executed
./run_migrations.py status
```

### Rollback (Record Only)

```bash
# Remove migration records (doesn't undo schema changes)
./run_migrations.py rollback 001_initial_schema.sql
```

**⚠️ Important**: Rollback only removes migration tracking records. It does not undo actual schema changes. Manual schema rollback would be required.

## Schema Overview

### Core Domains

1. **Identity Domain**
   - Users and profiles
   - Authentication and MFA
   - SSO provider integration

2. **Authorization Domain**
   - Dynamic RBAC with resource-based permissions
   - Role hierarchies and inheritance
   - Temporal and conditional permissions
   - Permission delegation

3. **LLM Domain**
   - Multiple LLM provider support
   - Conversation and message management
   - Document processing and analysis
   - Prompt template management
   - Usage tracking and cost analytics

4. **Analytics Domain**
   - Usage sessions and API monitoring
   - Business intelligence reporting
   - Cost allocation and budget management
   - Performance metrics

5. **Security Domain**
   - Data classification and masking
   - Encryption key management
   - Compliance framework support
   - PII detection and protection

6. **Audit Domain**
   - Comprehensive audit logging
   - Change tracking and versioning
   - Security event monitoring
   - Forensic capabilities

### Key Features

- **Dynamic RBAC**: Resource-based permissions with conditions
- **Multi-tenant Support**: Isolated data with shared infrastructure
- **Compliance Ready**: GDPR, HIPAA, SOX, PCI-DSS support
- **Audit Trail**: Complete change tracking and forensics
- **Cost Management**: Detailed usage and cost allocation
- **Security**: Data masking, encryption, and access controls

## Default Data

The seed migration creates:

### Roles
- `super_admin` - Full system access
- `admin` - Administrative access
- `manager` - Team management access
- `analyst` - Analytics and reporting
- `user` - Standard user access
- `viewer` - Read-only access
- `api_user` - Programmatic access
- `compliance_officer` - Compliance monitoring
- `security_admin` - Security management
- `cost_manager` - Budget management

### Resource Types
- System, User, Role, Permission
- Conversation, Message, Document
- Analytics, Audit, API
- Cost Center, Encryption Key, Compliance

### LLM Models
- GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo
- With pricing and capability configuration

### Compliance Frameworks
- GDPR, CCPA, HIPAA, SOX, PCI-DSS
- With requirements and controls

### Configuration Settings
- System defaults and service configurations
- Security policies and limits
- LLM and analytics settings

## Performance Considerations

### Indexing Strategy
- Comprehensive indexes for all query patterns
- Composite indexes for complex queries
- Partial indexes for filtered queries
- Foreign key indexes for joins

### Partitioning
Large tables are designed for partitioning:
- **audit_logs** - Monthly partitions
- **api_usage_logs** - Monthly partitions  
- **cost_allocations** - Monthly partitions
- **llm_usage_logs** - Monthly partitions

### Caching
Tables optimized for caching:
- Permission and role data
- Configuration settings
- User session data

## Security Features

### Data Protection
- Field-level encryption support
- Automatic PII detection and masking
- Data classification framework
- Compliance tracking

### Access Control
- Resource-based permissions
- Temporal access controls
- Delegation and proxy permissions
- Context-aware authorization

### Audit and Compliance
- Complete audit trail
- Change tracking with approval workflows
- Security event monitoring
- Compliance assessment framework

## Backup and Recovery

### Backup Strategy
- Point-in-time recovery capability
- Cross-region replication support
- Encrypted backup storage
- Long-term retention for compliance

### Recovery Procedures
1. Restore from backup
2. Run migrations to current version
3. Verify data integrity
4. Update application configuration

## Troubleshooting

### Common Issues

**Migration Fails with Permission Error**
```bash
# Ensure user has CREATE privileges
GRANT CREATE ON DATABASE enterprise_ai TO username;
```

**Extension Not Found**
```bash
# Install required extensions as superuser
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

**Connection Timeout**
```bash
# Check database URL and network connectivity
psql $DATABASE_URL -c "SELECT version();"
```

### Migration State Issues

**Reset Migration State** (⚠️ Destructive)
```sql
-- Only if you need to completely reset
DROP TABLE IF EXISTS schema_migrations;
```

**Check Migration Table**
```sql
SELECT * FROM schema_migrations ORDER BY id;
```

## Development

### Adding New Migrations

1. Create new migration file with sequential number
2. Follow naming convention: `XXX_description.sql`
3. Include rollback instructions in comments
4. Test on development database first
5. Update this README if needed

### Migration Best Practices

- Always backup before running migrations
- Test migrations on development environment
- Use transactions for atomic changes
- Include descriptive comments
- Consider performance impact of large changes
- Plan for rollback procedures

## Support

For issues with migrations:
1. Check PostgreSQL logs for detailed errors
2. Verify database permissions and extensions
3. Ensure Python dependencies are installed
4. Review migration file syntax
5. Check database connectivity and resources

## License

This migration system is part of the Enterprise AI System and follows the same licensing terms.

