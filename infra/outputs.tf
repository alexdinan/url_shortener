output "aws_region" {
    description = "The AWS region the app is deployed in"
    value = var.aws_region
}

output "ecr_url" {
    description = "URL for the AWS ECR image registry"
    value = aws_ecr_repository.backend.repository_url
}
