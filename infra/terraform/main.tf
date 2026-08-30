terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "production"
}

# 1. S3 Lakehouse Bucket for Oncology Telemetry & Claims
resource "aws_s3_bucket" "lakehouse_raw" {
  bucket        = "rhi-radion-lakehouse-raw-${var.environment}"
  force_destroy = false

  tags = {
    Environment = var.environment
    Domain      = "RadiationOncology"
    Project     = "GP-006-RHI-Radion"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lakehouse_raw_crypto" {
  bucket = aws_s3_bucket.lakehouse_raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 2. AWS Glue Data Catalog Database
resource "aws_glue_catalog_database" "oncology_catalog" {
  name        = "rhi_radion_oncology_lakehouse"
  description = "AWS Glue Catalog for RHI Radion Health Claims & Patient Protocols"
}

# 3. AWS Athena Analytics Workgroup
resource "aws_athena_workgroup" "oncology_workgroup" {
  name        = "rhi-radion-analytics-wg"
  description = "Workgroup for sub-second OLAP queries across DuckDB/Athena Lakehouse"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.lakehouse_raw.bucket}/athena_query_results/"
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}
