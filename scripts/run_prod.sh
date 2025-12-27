# go to root
cd ..

# ensure no uncommited changes
if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: Cannot deploy with uncommitted changes"
    exit 1
fi

# use latest git commit hash as image tag
GIT_HASH_TAG="$(git rev-parse --short HEAD)"

# provision AWS resources
cd infra
terraform init
terraform apply -auto-approve

# get outputs from terraform
AWS_REGION="$(terraform output -raw aws_region)"
ECR_URL="$(terraform output -raw ecr_url)"

cd ../backend
# authenticate docker to aws cli
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL
# build and tag docker image
docker build -t $ECR_URL:$GIT_HASH_TAG .
# push image to ECR
docker push $ECR_URL:$GIT_HASH_TAG
