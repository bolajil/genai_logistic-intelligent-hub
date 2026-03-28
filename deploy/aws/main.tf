# GLIH AWS Deployment - EKS + RDS + ElastiCache
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket         = "glih-terraform-state"
    key            = "aws/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "glih-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "GLIH"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ============================================================
# Variables
# ============================================================
variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

variable "cluster_name" {
  default = "glih-eks"
}

variable "db_instance_class" {
  default = "db.t3.medium"
}

variable "redis_node_type" {
  default = "cache.t3.micro"
}

# ============================================================
# VPC
# ============================================================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "glih-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment != "production"
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

# ============================================================
# EKS Cluster
# ============================================================
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    glih-nodes = {
      desired_capacity = 3
      max_capacity     = 6
      min_capacity     = 2

      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
    }
  }
}

# ============================================================
# RDS PostgreSQL
# ============================================================
resource "aws_db_subnet_group" "glih" {
  name       = "glih-db-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "rds" {
  name_prefix = "glih-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }
}

resource "aws_db_instance" "glih" {
  identifier        = "glih-postgres"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = var.db_instance_class
  allocated_storage = 100

  db_name  = "glih"
  username = "glih_admin"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.glih.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  skip_final_snapshot     = var.environment != "production"
  deletion_protection     = var.environment == "production"

  storage_encrypted = true
}

# ============================================================
# ElastiCache Redis
# ============================================================
resource "aws_elasticache_subnet_group" "glih" {
  name       = "glih-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "redis" {
  name_prefix = "glih-redis-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }
}

resource "aws_elasticache_cluster" "glih" {
  cluster_id           = "glih-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.glih.name
  security_group_ids = [aws_security_group.redis.id]
}

# ============================================================
# ECR Repository
# ============================================================
resource "aws_ecr_repository" "backend" {
  name                 = "glih-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "glih-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ============================================================
# AWS Secrets Manager — GLIH application secrets
# Stores JWT_SECRET, SENTRY_DSN, OPENAI_API_KEY, DATABASE_URL
# Backend reads these at startup via boto3 or as injected env vars
# ============================================================
resource "aws_secretsmanager_secret" "glih" {
  name                    = "glih/${var.environment}/app-secrets"
  description             = "GLIH application secrets — JWT, Sentry, OpenAI, DB credentials"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
}

resource "aws_secretsmanager_secret_version" "glih" {
  secret_id = aws_secretsmanager_secret.glih.id
  secret_string = jsonencode({
    JWT_SECRET     = "REPLACE_WITH_GENERATED_SECRET"   # python -c "import secrets; print(secrets.token_hex(32))"
    SENTRY_DSN     = ""                                 # Set after Sentry project created
    OPENAI_API_KEY = ""                                 # Set from OpenAI dashboard
    DATABASE_URL   = "postgresql://glih_admin:${var.db_password}@${aws_db_instance.glih.endpoint}/glih"
    REDIS_URL      = "redis://${aws_elasticache_cluster.glih.cache_nodes[0].address}:6379"
    GLIH_ENV       = var.environment
    RATE_LIMIT_QUERY  = "30/minute"
    RATE_LIMIT_AGENTS = "20/minute"
    RATE_LIMIT_INGEST = "10/minute"
  })

  lifecycle {
    ignore_changes = [secret_string]  # Prevent Terraform overwriting manual secret updates
  }
}

# IAM policy allowing EKS pods to read secrets
resource "aws_iam_policy" "glih_secrets" {
  name = "glih-secrets-read-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
      Resource = aws_secretsmanager_secret.glih.arn
    }]
  })
}

# ============================================================
# Outputs
# ============================================================
output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value = aws_db_instance.glih.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.glih.cache_nodes[0].address
}

output "ecr_backend_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "secrets_manager_arn" {
  value       = aws_secretsmanager_secret.glih.arn
  description = "ARN of Secrets Manager secret — use with EKS service account IAM role"
}
