#!/bin/bash

# AWS Deployment Script for Enterprise AI System
# Deploys the complete infrastructure and application to AWS

set -e

# Configuration
ENVIRONMENT=${1:-production}
AWS_REGION=${2:-us-east-1}
STACK_PREFIX="enterprise-ai"
PROJECT_NAME="enterprise-ai-system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Please run 'aws configure' first."
    fi
    
    success "Prerequisites check passed"
}

# Get AWS account ID
get_account_id() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log "AWS Account ID: $AWS_ACCOUNT_ID"
}

# Create ECR repository if it doesn't exist
create_ecr_repository() {
    log "Creating ECR repository..."
    
    REPO_NAME="${PROJECT_NAME}"
    
    if ! aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION &> /dev/null; then
        aws ecr create-repository \
            --repository-name $REPO_NAME \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        
        success "ECR repository created: $REPO_NAME"
    else
        log "ECR repository already exists: $REPO_NAME"
    fi
    
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"
}

# Build and push Docker image
build_and_push_image() {
    log "Building and pushing Docker image..."
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Build image
    docker build -f aws/docker/Dockerfile -t $PROJECT_NAME:latest ../
    
    # Tag image
    docker tag $PROJECT_NAME:latest $ECR_URI:latest
    docker tag $PROJECT_NAME:latest $ECR_URI:$ENVIRONMENT
    
    # Push image
    docker push $ECR_URI:latest
    docker push $ECR_URI:$ENVIRONMENT
    
    success "Docker image pushed to ECR: $ECR_URI:$ENVIRONMENT"
}

# Deploy CloudFormation stack
deploy_stack() {
    local stack_name=$1
    local template_file=$2
    local parameters_file=$3
    
    log "Deploying stack: $stack_name"
    
    local parameters=""
    if [ -f "$parameters_file" ]; then
        parameters="--parameters file://$parameters_file"
    fi
    
    aws cloudformation deploy \
        --template-file $template_file \
        --stack-name $stack_name \
        --parameter-overrides Environment=$ENVIRONMENT $parameters \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region $AWS_REGION \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
    
    success "Stack deployed: $stack_name"
}

# Get VPC information (assumes default VPC or existing VPC)
get_vpc_info() {
    log "Getting VPC information..."
    
    # Get default VPC
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWS_REGION)
    
    if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
        error "No default VPC found. Please create a VPC first or specify VPC ID."
    fi
    
    # Get subnets
    PUBLIC_SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" \
        --query "Subnets[].SubnetId" --output text --region $AWS_REGION | tr '\t' ',')
    
    PRIVATE_SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=false" \
        --query "Subnets[].SubnetId" --output text --region $AWS_REGION | tr '\t' ',')
    
    # If no private subnets, use public subnets
    if [ -z "$PRIVATE_SUBNETS" ]; then
        PRIVATE_SUBNETS=$PUBLIC_SUBNETS
        warning "No private subnets found, using public subnets for private resources"
    fi
    
    log "VPC ID: $VPC_ID"
    log "Public Subnets: $PUBLIC_SUBNETS"
    log "Private Subnets: $PRIVATE_SUBNETS"
}

# Create parameter files
create_parameter_files() {
    log "Creating parameter files..."
    
    # RDS parameters
    cat > /tmp/rds-parameters.json << EOF
[
    {
        "ParameterKey": "VpcId",
        "ParameterValue": "$VPC_ID"
    },
    {
        "ParameterKey": "PrivateSubnetIds",
        "ParameterValue": "$PRIVATE_SUBNETS"
    }
]
EOF

    # ECS parameters
    cat > /tmp/ecs-parameters.json << EOF
[
    {
        "ParameterKey": "VpcId",
        "ParameterValue": "$VPC_ID"
    },
    {
        "ParameterKey": "PublicSubnetIds",
        "ParameterValue": "$PUBLIC_SUBNETS"
    },
    {
        "ParameterKey": "PrivateSubnetIds",
        "ParameterValue": "$PRIVATE_SUBNETS"
    },
    {
        "ParameterKey": "ImageUri",
        "ParameterValue": "$ECR_URI:$ENVIRONMENT"
    }
]
EOF
}

# Main deployment function
main() {
    log "Starting AWS deployment for Enterprise AI System"
    log "Environment: $ENVIRONMENT"
    log "Region: $AWS_REGION"
    
    check_prerequisites
    get_account_id
    get_vpc_info
    create_ecr_repository
    build_and_push_image
    create_parameter_files
    
    # Deploy stacks in order
    log "Deploying infrastructure stacks..."
    
    # 1. IAM Roles
    deploy_stack "${ENVIRONMENT}-${STACK_PREFIX}-iam" "iam/iam-roles.yaml"
    
    # 2. Secrets Manager
    deploy_stack "${ENVIRONMENT}-${STACK_PREFIX}-secrets" "secrets/secrets-manager-config.yaml"
    
    # 3. RDS Database
    deploy_stack "${ENVIRONMENT}-${STACK_PREFIX}-rds" "rds/rds-postgres-config.yaml" "/tmp/rds-parameters.json"
    
    # Wait for RDS to be available
    log "Waiting for RDS instance to be available..."
    aws rds wait db-instance-available --db-instance-identifier "${ENVIRONMENT}-enterprise-ai-db" --region $AWS_REGION
    
    # Get RDS endpoint and other outputs
    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "${ENVIRONMENT}-${STACK_PREFIX}-rds" \
        --query "Stacks[0].Outputs[?OutputKey=='DBInstanceEndpoint'].OutputValue" \
        --output text --region $AWS_REGION)
    
    APP_SECURITY_GROUP=$(aws cloudformation describe-stacks \
        --stack-name "${ENVIRONMENT}-${STACK_PREFIX}-rds" \
        --query "Stacks[0].Outputs[?OutputKey=='AppSecurityGroupId'].OutputValue" \
        --output text --region $AWS_REGION)
    
    DB_PASSWORD_SECRET=$(aws cloudformation describe-stacks \
        --stack-name "${ENVIRONMENT}-${STACK_PREFIX}-rds" \
        --query "Stacks[0].Outputs[?OutputKey=='DBPasswordSecretArn'].OutputValue" \
        --output text --region $AWS_REGION)
    
    # Update ECS parameters with RDS outputs
    cat > /tmp/ecs-parameters.json << EOF
[
    {
        "ParameterKey": "VpcId",
        "ParameterValue": "$VPC_ID"
    },
    {
        "ParameterKey": "PublicSubnetIds",
        "ParameterValue": "$PUBLIC_SUBNETS"
    },
    {
        "ParameterKey": "PrivateSubnetIds",
        "ParameterValue": "$PRIVATE_SUBNETS"
    },
    {
        "ParameterKey": "ImageUri",
        "ParameterValue": "$ECR_URI:$ENVIRONMENT"
    },
    {
        "ParameterKey": "AppSecurityGroupId",
        "ParameterValue": "$APP_SECURITY_GROUP"
    },
    {
        "ParameterKey": "DBEndpoint",
        "ParameterValue": "$DB_ENDPOINT"
    },
    {
        "ParameterKey": "DBPasswordSecretArn",
        "ParameterValue": "$DB_PASSWORD_SECRET"
    }
]
EOF
    
    # 4. ECS Service
    deploy_stack "${ENVIRONMENT}-${STACK_PREFIX}-ecs" "ecs/ecs-service-config.yaml" "/tmp/ecs-parameters.json"
    
    # Get ECS outputs for monitoring
    ECS_CLUSTER=$(aws cloudformation describe-stacks \
        --stack-name "${ENVIRONMENT}-${STACK_PREFIX}-ecs" \
        --query "Stacks[0].Outputs[?OutputKey=='ECSClusterName'].OutputValue" \
        --output text --region $AWS_REGION)
    
    ECS_SERVICE=$(aws cloudformation describe-stacks \
        --stack-name "${ENVIRONMENT}-${STACK_PREFIX}-ecs" \
        --query "Stacks[0].Outputs[?OutputKey=='ECSServiceName'].OutputValue" \
        --output text --region $AWS_REGION)
    
    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name "${ENVIRONMENT}-${STACK_PREFIX}-ecs" \
        --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
        --output text --region $AWS_REGION)
    
    # Create monitoring parameters
    cat > /tmp/monitoring-parameters.json << EOF
[
    {
        "ParameterKey": "ECSClusterName",
        "ParameterValue": "$ECS_CLUSTER"
    },
    {
        "ParameterKey": "ECSServiceName",
        "ParameterValue": "$ECS_SERVICE"
    },
    {
        "ParameterKey": "LoadBalancerFullName",
        "ParameterValue": "app/${ENVIRONMENT}-enterprise-ai-alb/$(echo $ALB_DNS | cut -d'-' -f3-)"
    },
    {
        "ParameterKey": "DBInstanceIdentifier",
        "ParameterValue": "${ENVIRONMENT}-enterprise-ai-db"
    }
]
EOF
    
    # 5. CloudWatch Monitoring
    deploy_stack "${ENVIRONMENT}-${STACK_PREFIX}-monitoring" "cloudwatch/monitoring-config.yaml" "/tmp/monitoring-parameters.json"
    
    # Wait for ECS service to be stable
    log "Waiting for ECS service to be stable..."
    aws ecs wait services-stable --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION
    
    # Clean up temporary files
    rm -f /tmp/*-parameters.json
    
    success "Deployment completed successfully!"
    
    log "Application URL: http://$ALB_DNS"
    log "Health Check: http://$ALB_DNS/health"
    log "API Documentation: http://$ALB_DNS/docs"
    
    log "CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${ENVIRONMENT}-enterprise-ai-dashboard"
    
    log "To test the deployment:"
    log "curl http://$ALB_DNS/health"
}

# Run main function
main "$@"

