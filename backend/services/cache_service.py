import os
import json
from typing import Any, Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Lazy DynamoDB resource creation. Support LocalStack for local development.
TABLE_NAME = os.getenv("INSTRUMENTS_TABLE", "InstrumentsCache")
USE_LOCALSTACK = os.getenv("USE_LOCALSTACK", "false").lower() == "true"

_table = None
_local_cache: dict[str, Any] = {}

def _init_table():
    global _table
    if _table is not None:
        return
    try:
        import boto3

        # Configure for LocalStack if enabled
        if USE_LOCALSTACK:
            logger.info("Using LocalStack for DynamoDB")
            dynamodb = boto3.resource(
                "dynamodb",
                endpoint_url="http://localhost:4566",
                region_name="us-east-1",
                aws_access_key_id="test",
                aws_secret_access_key="test"
            )
        else:
            # Production AWS configuration
            region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
            if region:
                session = boto3.session.Session(region_name=region)
                dynamodb = session.resource("dynamodb")
            else:
                # no region configured; attempt default resource which may still work if env is set later
                dynamodb = boto3.resource("dynamodb")
        
        _table = dynamodb.Table(TABLE_NAME)
        
        # Test table access
        _table.load()
        logger.info(f"Connected to DynamoDB table: {TABLE_NAME}")
        
    except Exception as e:
        logger.warning("DynamoDB not available, using local in-memory cache: %s", e)
        _table = None


async def get_cached(key: str) -> Optional[Any]:
    _init_table()
    if _table is None:
        # local in-memory fallback
        return _local_cache.get(key)
    try:
        resp = _table.get_item(Key={"pk": key})
        item = resp.get("Item")
        if item:
            return json.loads(item["data"])
    except Exception as e:
        logger.warning("Cache get failed: %s", e)
    return None


async def put_cached(key: str, value: Any):
    _init_table()
    if _table is None:
        _local_cache[key] = value
        return
    try:
        _table.put_item(Item={"pk": key, "data": json.dumps(value)})
    except Exception as e:
        logger.warning("Cache put failed: %s", e)
