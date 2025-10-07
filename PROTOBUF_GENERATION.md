# Alternative methods to regenerate protobuf files if needed
# (Only needed if MarketDataFeed.proto is updated)

# Method 1: Using protoc directly (if installed)
# protoc --python_out=. backend/proto/MarketDataFeed.proto

# Method 2: Using Docker (cross-platform solution)
# docker run --rm -v ${PWD}:/workspace -w /workspace namely/protoc-all -l python -d . backend/proto/MarketDataFeed.proto

# Method 3: Install protoc compiler separately
# Download from: https://github.com/protocolbuffers/protobuf/releases
# Add to PATH and run: protoc --python_out=backend/proto backend/proto/MarketDataFeed.proto

# Current generated files (no need to regenerate unless .proto changes):
# - backend/proto/MarketDataFeed_pb2.py

# Note: grpcio-tools was removed from requirements.txt due to Windows compilation issues
# The generated protobuf files are sufficient for runtime operations