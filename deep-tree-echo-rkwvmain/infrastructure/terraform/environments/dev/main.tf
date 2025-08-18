terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket         = "deep-echo-terraform-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "deep-echo-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "development"
      Project     = "deep-tree-echo"
      ManagedBy   = "terraform"
      Owner       = "devops-team"
    }
  }
}

module "deep_echo" {
  source = "../"
  
  # Environment configuration
  environment = "dev"
  aws_region  = "us-west-2"
  
  # VPC configuration
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b"]
  
  # EKS configuration
  kubernetes_version = "1.27"
  node_groups = {
    general = {
      instance_types = ["t3.small"]
      scaling_config = {
        desired_size = 1
        max_size     = 3
        min_size     = 1
      }
      capacity_type = "ON_DEMAND"
    }
  }
  
  # Database configuration
  db_instance_class           = "db.t3.micro"
  db_allocated_storage        = 20
  db_max_allocated_storage    = 50
  db_backup_retention_period  = 3
  
  # Redis configuration
  redis_node_type = "cache.t3.micro"
  
  # Monitoring configuration
  log_retention_days = 7
  
  # S3 lifecycle configuration
  s3_lifecycle_rules = [
    {
      id                                  = "dev_lifecycle"
      enabled                            = true
      filter_prefix                      = "logs/"
      transition_days                    = 7
      transition_storage_class           = "STANDARD_IA"
      expiration_days                    = 30
      noncurrent_version_expiration_days = 7
    }
  ]
}