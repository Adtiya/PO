# AWS Deployment Guide for Enterprise AI System

This directory contains all the necessary configurations and scripts to deploy the Enterprise AI System on AWS with production-ready infrastructure.

## 🏗️ Architecture Overview

The AWS deployment includes:

- **RDS PostgreSQL**: Managed database with high availability and automated backups
- **ECS Fargate**: Containerized application deployment with auto-scaling
- **Application Load Balancer**: Traffic distribution and SSL termination
- **ElastiCache Redis**: Caching and session management
- **Secrets Manager**: Secure storage of sensitive configuration
- **CloudWatch**: Comprehensive monitoring and alerting
- **IAM Roles**: Least privilege security model

## 📁 Directory Structure

```
aws/
├── rds/                    # RDS PostgreSQL configuration
├── ecs/                    # ECS service and task definitions
├── iam/                    # IAM roles and policies
├── secrets/                # Secrets Manager configuration
├── cloudwatch/             # Monitoring and alerting
├── docker/                 # Docker configuration
├── deploy.sh              # Automated deployment script
└── README.md              # This file
```

## 🚀 Quick Deployment

### Prerequisites

1. **AWS CLI** installed and configured
2. **Docker** installed and running
3. **AWS credentials** configured with appropriate permissions
4. **Default VPC** or existing VPC in your AWS account

### One-Command Deployment

```bash
# Deploy to production
./deploy.sh production us-east-1

# Deploy to staging
./deploy.sh staging us-west-2
```

The deployment script will:
1. ✅ Check prerequisites
2. 🏗️ Create ECR repository
3. 🐳 Build and push Docker image
4. 🛡️ Deploy IAM roles and policies
5. 🔐 Set up Secrets Manager
6. 🗄️ Create RDS PostgreSQL instance
7. 🚀 Deploy ECS service with load balancer
8. 📊 Configure CloudWatch monitoring
9. ✅ Verify deployment health

## 🔧 Manual Deployment Steps

If you prefer to deploy components individually:

### 1. Build and Push Docker Image

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

# Create ECR repository
aws ecr create-repository --repository-name enterprise-ai-system --region $AWS_REGION

# Build and push image
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -f docker/Dockerfile -t enterprise-ai-system:latest ../../
docker tag enterprise-ai-system:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/enterprise-ai-system:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/enterprise-ai-system:latest
```

### 2. Deploy Infrastructure Stacks

```bash
# Deploy IAM roles
aws cloudformation deploy \
  --template-file iam/iam-roles.yaml \
  --stack-name production-enterprise-ai-iam \
  --parameter-overrides Environment=production \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Deploy Secrets Manager
aws cloudformation deploy \
  --template-file secrets/secrets-manager-config.yaml \
  --stack-name production-enterprise-ai-secrets \
  --parameter-overrides Environment=production

# Deploy RDS (requires VPC parameters)
aws cloudformation deploy \
  --template-file rds/rds-postgres-config.yaml \
  --stack-name production-enterprise-ai-rds \
  --parameter-overrides Environment=production VpcId=vpc-xxxxxx PrivateSubnetIds=subnet-xxxxx,subnet-yyyyy

# Deploy ECS service (requires all previous stack outputs)
aws cloudformation deploy \
  --template-file ecs/ecs-service-config.yaml \
  --stack-name production-enterprise-ai-ecs \
  --parameter-overrides Environment=production [... other parameters]

# Deploy monitoring
aws cloudformation deploy \
  --template-file cloudwatch/monitoring-config.yaml \
  --stack-name production-enterprise-ai-monitoring \
  --parameter-overrides Environment=production [... other parameters]
```

## 🔐 Security Configuration

### Secrets Management

The system uses AWS Secrets Manager for sensitive data:

- Database passwords (auto-generated)
- JWT secret keys
- API keys for external services
- SSL certificates
- OAuth configuration

### Network Security

- Application runs in private subnets
- Database accessible only from application security group
- Load balancer in public subnets with restricted access
- All traffic encrypted in transit

### IAM Security

- Least privilege principle applied
- Separate roles for different components
- No hardcoded credentials in code or containers

## 📊 Monitoring and Alerting

### CloudWatch Metrics

- **Application**: CPU, memory, response time, error rate
- **Database**: CPU, connections, storage, performance
- **Load Balancer**: Request count, latency, error rates
- **Custom**: Authentication failures, business metrics

### Alerts

Automatic alerts for:
- High CPU/memory usage
- Database connection issues
- Application errors
- Authentication failures
- Storage space warnings

### Dashboard

Comprehensive CloudWatch dashboard with:
- Real-time metrics visualization
- Log analysis and error tracking
- Performance trends
- System health overview

## 🔄 Auto Scaling

### ECS Service Auto Scaling

- **Target Tracking**: CPU and memory utilization
- **Scale Out**: Add tasks when load increases
- **Scale In**: Remove tasks when load decreases
- **Min/Max**: Configurable task count limits

### Database Scaling

- **Read Replicas**: For read-heavy workloads
- **Storage Auto Scaling**: Automatic storage expansion
- **Performance Insights**: Query performance monitoring

## 🚀 Deployment Environments

### Development
- Single AZ deployment
- Smaller instance sizes
- Shorter backup retention
- Basic monitoring

### Staging
- Multi-AZ for testing
- Production-like configuration
- Extended monitoring
- Blue/green deployment testing

### Production
- Multi-AZ high availability
- Enhanced monitoring
- Automated backups
- Performance insights
- DDoS protection

## 🔧 Configuration

### Environment Variables

The application supports these environment variables:

```bash
# Database
DATABASE_HOST=your-rds-endpoint
DATABASE_PORT=5432
DATABASE_NAME=enterprise_ai
DATABASE_USER=enterprise_admin
DATABASE_PASSWORD=from-secrets-manager

# Redis
REDIS_HOST=your-elasticache-endpoint
REDIS_PORT=6379

# Application
ENVIRONMENT=production
SECRET_KEY=from-secrets-manager
JWT_SECRET_KEY=from-secrets-manager

# AWS
AWS_DEFAULT_REGION=us-east-1
```

### Customization

You can customize the deployment by modifying:

- **Instance sizes**: Update CloudFormation parameters
- **Auto scaling**: Adjust scaling policies
- **Monitoring**: Add custom metrics and alarms
- **Security**: Modify security groups and IAM policies

## 🛠️ Maintenance

### Updates

```bash
# Update application
./deploy.sh production us-east-1

# Update specific stack
aws cloudformation deploy --template-file ecs/ecs-service-config.yaml --stack-name production-enterprise-ai-ecs
```

### Backups

- **Database**: Automated daily backups with point-in-time recovery
- **Application**: Stateless, no backup needed
- **Configuration**: Version controlled in Git

### Monitoring

- Check CloudWatch dashboard regularly
- Review CloudWatch Logs for errors
- Monitor cost and usage reports
- Set up billing alerts

## 🆘 Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check AWS credentials and permissions
   - Verify VPC and subnet configuration
   - Review CloudFormation events

2. **Application Not Accessible**
   - Check security group rules
   - Verify load balancer health checks
   - Review ECS service logs

3. **Database Connection Issues**
   - Check security group connectivity
   - Verify credentials in Secrets Manager
   - Review RDS parameter group settings

### Logs

```bash
# View ECS service logs
aws logs tail /ecs/production-enterprise-ai --follow

# View specific task logs
aws ecs describe-tasks --cluster production-enterprise-ai-cluster --tasks task-id
```

### Health Checks

```bash
# Check application health
curl http://your-alb-dns/health

# Check database connectivity
aws rds describe-db-instances --db-instance-identifier production-enterprise-ai-db
```

## 💰 Cost Optimization

### Recommendations

1. **Right-sizing**: Monitor and adjust instance sizes
2. **Reserved Instances**: For predictable workloads
3. **Spot Instances**: For non-critical tasks
4. **Storage Optimization**: Use appropriate storage types
5. **Monitoring**: Set up cost alerts and budgets

### Cost Breakdown

Estimated monthly costs (us-east-1):

- **RDS db.t3.medium**: ~$60
- **ECS Fargate (2 tasks)**: ~$50
- **Application Load Balancer**: ~$20
- **ElastiCache**: ~$15
- **Data Transfer**: ~$10
- **CloudWatch**: ~$5

**Total**: ~$160/month (varies by usage)

## 📞 Support

For deployment issues or questions:

1. Check CloudFormation events and stack outputs
2. Review CloudWatch logs and metrics
3. Consult AWS documentation
4. Contact your AWS support team

## 🔄 CI/CD Integration

This deployment can be integrated with CI/CD pipelines:

- **GitHub Actions**: Use provided workflows
- **AWS CodePipeline**: Deploy on code changes
- **Jenkins**: Custom deployment jobs
- **GitLab CI**: Automated deployments

---

**🎉 Congratulations!** You now have a production-ready Enterprise AI System deployed on AWS with enterprise-grade security, monitoring, and scalability.

