#!/bin/bash

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
while ! awslocal dynamodb list-tables >/dev/null 2>&1; do
    echo "Waiting for DynamoDB..."
    sleep 1
done

echo "Creating DynamoDB tables..."

# Create InstrumentsCache table
awslocal dynamodb create-table \
    --table-name InstrumentsCache \
    --attribute-definitions \
        AttributeName=pk,AttributeType=S \
    --key-schema \
        AttributeName=pk,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

echo "InstrumentsCache table created"

# Create general cache table for other app data
awslocal dynamodb create-table \
    --table-name AlgoTradingCache \
    --attribute-definitions \
        AttributeName=pk,AttributeType=S \
    --key-schema \
        AttributeName=pk,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

echo "AlgoTradingCache table created"

# Create S3 bucket for potential file storage
awslocal s3api create-bucket \
    --bucket algo-trading-dev \
    --region us-east-1

echo "S3 bucket created"

# List created resources
echo "\nCreated DynamoDB tables:"
awslocal dynamodb list-tables

echo "\nCreated S3 buckets:"
awslocal s3api list-buckets

echo "LocalStack initialization complete!"
