# create ecr image repo and attach image lifecycle policy
resource "aws_ecr_repository" "backend" {
    name = "backend-docker-image-repo"

    image_scanning_configuration {
        # scan images for vulnerabilities on push
        scan_on_push = true
    }

    lifecycle {
        # prevents deletion of production image repo
        prevent_destroy = true
    }

}

resource "aws_ecr_lifecycle_policy" "backend" {
    # clean up old images. store only the N most recent
    repository = aws_ecr_repository.backend.name

    policy = jsonencode({
        rules = [
            {
                rulePriority = 1
                description = "Keep the N most recently pushed images"
                selection = {
                    tagStatus = "any"
                    countType = "imageCountMoreThan"
                    countNumber = var.ecr_capacity
                }
                action = {
                    type = "expire"
                }
            }
        ]
    })
}
