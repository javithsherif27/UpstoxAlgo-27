"""
Test script to verify protobuf functionality without grpcio-tools
"""

def test_protobuf_import():
    """Test if we can import and use protobuf classes"""
    print("Testing protobuf functionality...")
    
    try:
        # Test basic protobuf import
        import google.protobuf
        print(f"✅ protobuf library version: {google.protobuf.__version__}")
        
        # Test our generated protobuf classes
        try:
            from backend.proto.MarketDataFeed_pb2 import FeedResponse, Feed, LTPC
            print("✅ MarketDataFeed protobuf classes imported successfully")
            
            # Test creating a simple protobuf message
            feed_response = FeedResponse()
            print("✅ FeedResponse object created successfully")
            
            return True
            
        except ImportError as e:
            print(f"❌ Failed to import MarketDataFeed protobuf classes: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import protobuf library: {e}")
        return False

def test_websocket_client_import():
    """Test if WebSocket client can be imported without grpcio-tools"""
    print("\nTesting WebSocket client import...")
    
    try:
        from backend.services.websocket_client import UpstoxWebSocketClient
        print("✅ UpstoxWebSocketClient imported successfully")
        
        # Test creating client instance
        client = UpstoxWebSocketClient()
        print("✅ WebSocket client instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import/create WebSocket client: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Dependencies After grpcio-tools Removal")
    print("=" * 60)
    
    protobuf_ok = test_protobuf_import()
    websocket_ok = test_websocket_client_import()
    
    print("\n" + "=" * 60)
    if protobuf_ok and websocket_ok:
        print("🎉 SUCCESS: All dependencies work without grpcio-tools!")
        print("Your application should start without compilation errors now.")
    else:
        print("❌ ISSUES DETECTED: Some functionality may not work.")
        
    print("\n📋 Next Steps:")
    print("1. Run: .\\start-local.bat")
    print("2. The application should start without compilation errors")
    print("3. WebSocket data parsing will work normally")