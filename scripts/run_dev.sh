
# load environment variables
source ../.env.local

echo "starting containers..."

# start backend and dyamodb-local container
docker-compose --env-file ../.env.local -f ../docker-compose.yml up --build -d

# wait for dynamodb-local to be ready
sleep 3

echo "Creating table within dynamodb container"

# create table within dynamodb
aws dynamodb create-table \
    --table-name url_mappings \
    --attribute-definitions \
        AttributeName=short_code,AttributeType=S \
    --key-schema \
        AttributeName=short_code,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --endpoint-url http://localhost:$DYNAMODB_HOST_PORT \
    --region eu-west-2 --no-cli-pager

echo "Adding expires_at ttl attribute"

# enable ttl on the table for expires_at attribute
aws dynamodb update-time-to-live \
    --table-name url_mappings \
    --time-to-live-specification Enabled=true,AttributeName=expires_at \
    --endpoint-url http://localhost:$DYNAMODB_HOST_PORT \
    --region eu-west-2

echo "SUCCESS: to shut down app: docker-compose down"
