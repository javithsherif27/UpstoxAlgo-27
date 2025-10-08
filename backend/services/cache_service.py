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
_cache_file = "local_cache.json"

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


def _load_local_cache():
    """Load cache from file if it exists"""
    global _local_cache
    try:
        if os.path.exists(_cache_file):
            with open(_cache_file, 'r') as f:
                _local_cache = json.load(f)
                logger.info(f"Loaded local cache from {_cache_file}")
        else:
            _local_cache = {}
    except Exception as e:
        logger.warning(f"Failed to load local cache: {e}")
        _local_cache = {}

def _save_local_cache():
    """Save cache to file"""
    try:
        with open(_cache_file, 'w') as f:
            json.dump(_local_cache, f, indent=2)
        logger.debug(f"Saved local cache to {_cache_file}")
    except Exception as e:
        logger.warning(f"Failed to save local cache: {e}")

async def get_cached(key: str) -> Optional[Any]:
    _init_table()
    if _table is None:
        # Load cache from file if not already loaded
        if not _local_cache:
            _load_local_cache()
        # local file-backed cache fallback
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
        # Load cache from file if not already loaded
        if not _local_cache:
            _load_local_cache()
        _local_cache[key] = value
        _save_local_cache()  # Persist to file immediately
        return
    try:
        _table.put_item(Item={"pk": key, "data": json.dumps(value)})
    except Exception as e:
        logger.warning("Cache put failed: %s", e)
