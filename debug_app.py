#!/usr/bin/env python3

import sys
import traceback

try:
    # Import our backend app
    sys.path.append('.')
    from backend.app import app
    print("✅ Backend app imported successfully")
    
    # Try to access some basic app properties
    print(f"✅ App title: {app.title}")
    print(f"✅ Number of routes: {len(app.routes)}")
    
    # List all routes
    print("\n📍 Available routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {route.methods} {route.path}")
        elif hasattr(route, 'path'):
            print(f"  {route.path}")
    
except Exception as e:
    print(f"❌ Error during app import/inspection:")
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()