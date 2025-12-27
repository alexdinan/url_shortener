# provision AWS resources
cd ../infra
terraform init
terraform plan
terraform apply -auto-approve

# build backend docker image
cd ../backend
docker build tinyurl-app .
docke push

# push to ECR