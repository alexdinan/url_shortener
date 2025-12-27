variable "aws_region" {
    type = string
    description = "AWS region for app deployment"
}

variable "ecr_capacity" {
    type = number
    description = "The maximum no. images the ECR repository should store"
}
