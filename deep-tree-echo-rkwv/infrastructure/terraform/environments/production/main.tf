terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket         = "deep-echo-terraform-state-prod"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "deep-echo-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "production"
      Project     = "deep-tree-echo"
      ManagedBy   = "terraform"
      Owner       = "devops-team"
      CostCenter  = "engineering"
    }
  }
}

module "deep_echo" {
  source = "../"
  
  # Environment configuration
  environment = "production"
  aws_region  = "us-west-2"
  
  # VPC configuration
  vpc_cidr           = "10.1.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
  
  # EKS configuration
  kubernetes_version = "1.27"
  node_groups = {
    general = {
      instance_types = ["t3.large"]
      scaling_config = {
        desired_size = 3
        max_size     = 20
        min_size     = 3
      }
      capacity_type = "ON_DEMAND"
    }
    spot = {
      instance_types = ["t3.large", "t3.xlarge"]
      scaling_config = {
        desired_size = 2
        max_size     = 10
        min_size     = 0
      }
      capacity_type = "SPOT"
    }
    high_memory = {
      instance_types = ["r5.large"]
      scaling_config = {
        desired_size = 1
        max_size     = 5
        min_size     = 1
      }
      capacity_type = "ON_DEMAND"
    }
  }
  
  # Database configuration
  db_instance_class           = "db.r5.large"
  db_allocated_storage        = 100
  db_max_allocated_storage    = 1000
  db_backup_retention_period  = 30
  db_backup_window           = "03:00-04:00"
  db_maintenance_window      = "sun:04:00-sun:05:00"
  
  # Redis configuration
  redis_node_type = "cache.r5.large"
  
  # DNS configuration
  domain_name = "deepecho.ai"
  
  # Monitoring configuration
  log_retention_days = 90
  
  # S3 lifecycle configuration
  s3_lifecycle_rules = [
    {
      id                                  = "prod_lifecycle"
      enabled                            = true
      filter_prefix                      = "logs/"
      transition_days                    = 30
      transition_storage_class           = "STANDARD_IA"
      expiration_days                    = 365
      noncurrent_version_expiration_days = 90
    },
    {
      id                                  = "backup_lifecycle"
      enabled                            = true
      filter_prefix                      = "backups/"
      transition_days                    = 7
      transition_storage_class           = "GLACIER"
      expiration_days                    = 2555  # 7 years
      noncurrent_version_expiration_days = 30
    }
  ]
}