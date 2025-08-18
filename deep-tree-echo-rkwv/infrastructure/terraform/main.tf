terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name               = var.project_name
  environment        = var.environment
  cidr               = var.vpc_cidr
  availability_zones = var.availability_zones
  
  enable_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = local.common_tags
}

# EKS Cluster Module
module "eks" {
  source = "./modules/eks"
  
  cluster_name     = "${var.project_name}-${var.environment}"
  cluster_version  = var.kubernetes_version
  
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets
  
  node_groups = var.node_groups
  
  enable_irsa = true
  
  tags = local.common_tags
}

# RDS Module for persistent storage
module "rds" {
  source = "./modules/rds"
  
  identifier = "${var.project_name}-${var.environment}"
  
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = var.db_instance_class
  
  db_name  = var.db_name
  username = var.db_username
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  
  vpc_security_group_ids = [module.security_groups.rds_sg_id]
  db_subnet_group_name   = module.vpc.database_subnet_group
  
  backup_retention_period = var.db_backup_retention_period
  backup_window          = var.db_backup_window
  maintenance_window     = var.db_maintenance_window
  
  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment != "production" ? true : false
  
  tags = local.common_tags
}

# ElastiCache Redis Module
module "redis" {
  source = "./modules/redis"
  
  cluster_id = "${var.project_name}-${var.environment}-redis"
  
  node_type               = var.redis_node_type
  port                   = 6379
  parameter_group_name   = "default.redis7"
  
  subnet_group_name       = module.vpc.elasticache_subnet_group
  security_group_ids      = [module.security_groups.redis_sg_id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = local.common_tags
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security_groups"
  
  name_prefix = "${var.project_name}-${var.environment}"
  vpc_id      = module.vpc.vpc_id
  
  tags = local.common_tags
}

# ALB Module
module "alb" {
  source = "./modules/alb"
  
  name = "${var.project_name}-${var.environment}-alb"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets
  
  security_group_ids = [module.security_groups.alb_sg_id]
  
  enable_http2                     = true
  enable_cross_zone_load_balancing = true
  enable_deletion_protection       = var.environment == "production" ? true : false
  
  tags = local.common_tags
}

# S3 Buckets for storage and backups
module "s3" {
  source = "./modules/s3"
  
  project_name = var.project_name
  environment  = var.environment
  
  enable_versioning = true
  enable_encryption = true
  
  lifecycle_rules = var.s3_lifecycle_rules
  
  tags = local.common_tags
}

# CloudWatch Monitoring
module "monitoring" {
  source = "./modules/monitoring"
  
  project_name = var.project_name
  environment  = var.environment
  
  cluster_name = module.eks.cluster_name
  rds_identifier = module.rds.db_instance_identifier
  redis_cluster_id = module.redis.cluster_id
  
  enable_log_groups = true
  log_retention_days = var.log_retention_days
  
  tags = local.common_tags
}

# Route53 DNS
module "dns" {
  source = "./modules/dns"
  count  = var.domain_name != "" ? 1 : 0
  
  domain_name = var.domain_name
  environment = var.environment
  
  alb_dns_name    = module.alb.dns_name
  alb_zone_id     = module.alb.zone_id
  
  tags = local.common_tags
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "deep-tree-echo-rkwv"
  }
}