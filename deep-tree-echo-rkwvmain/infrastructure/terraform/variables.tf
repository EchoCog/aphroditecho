variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "deep-tree-echo"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.27"
}

variable "node_groups" {
  description = "EKS node groups configuration"
  type = map(object({
    instance_types = list(string)
    scaling_config = object({
      desired_size = number
      max_size     = number
      min_size     = number
    })
    capacity_type = string
  }))
  default = {
    general = {
      instance_types = ["t3.medium"]
      scaling_config = {
        desired_size = 2
        max_size     = 10
        min_size     = 1
      }
      capacity_type = "ON_DEMAND"
    }
    spot = {
      instance_types = ["t3.medium", "t3.large"]
      scaling_config = {
        desired_size = 1
        max_size     = 5
        min_size     = 0
      }
      capacity_type = "SPOT"
    }
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "deepecho"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "deepecho"
}

variable "db_allocated_storage" {
  description = "Database allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Database max allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_backup_retention_period" {
  description = "Database backup retention period in days"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Database backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Database maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "s3_lifecycle_rules" {
  description = "S3 lifecycle rules"
  type = list(object({
    id                                     = string
    enabled                               = bool
    filter_prefix                         = string
    transition_days                       = number
    transition_storage_class              = string
    expiration_days                       = number
    noncurrent_version_expiration_days    = number
  }))
  default = [
    {
      id                                  = "lifecycle_rule_1"
      enabled                            = true
      filter_prefix                      = "logs/"
      transition_days                    = 30
      transition_storage_class           = "STANDARD_IA"
      expiration_days                    = 90
      noncurrent_version_expiration_days = 30
    }
  ]
}