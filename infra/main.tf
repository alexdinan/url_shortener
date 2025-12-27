terraform {
    backend "s3" {
        bucket = "tiny-url-app-backend"
        key = "terraform.tfstate"
        region = "eu-west-2"
    }

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
