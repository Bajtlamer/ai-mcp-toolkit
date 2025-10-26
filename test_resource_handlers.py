#!/usr/bin/env python3
"""Test script to verify MCP resource handlers."""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_mcp_toolkit.models.database import db_manager
from ai_mcp_toolkit.managers.resource_manager import ResourceManager
from ai_mcp_toolkit.models.documents import ResourceType


async def test_resource_operations():
    """Test resource manager operations."""
    print("🚀 Testing Resource Manager Operations")
    print("=" * 50)
    
    try:
        # Connect to database
        await db_manager.connect()
        print("✅ Connected to database")
        
        # Initialize resource manager
        resource_manager = ResourceManager()
        
        # Test 1: Create a resource
        print("\n📝 Test 1: Creating a test resource...")
        test_uri = "test://example.com/test-resource.txt"
        resource = await resource_manager.create_resource(
            uri=test_uri,
            name="Test Resource",
            description="A test resource for verifying MCP handlers",
            mime_type="text/plain",
            resource_type=ResourceType.TEXT,
            content="This is test content for the MCP resource handler."
        )
        print(f"✅ Created resource: {resource.name} ({resource.uri})")
        
        # Test 2: List resources
        print("\n📋 Test 2: Listing resources...")
        list_result = await resource_manager.list_resources()
        print(f"✅ Found {len(list_result.resources)} resources:")
        for r in list_result.resources:
            print(f"   - {r.name} ({r.uri})")
        
        # Test 3: Read resource
        print(f"\n📖 Test 3: Reading resource '{test_uri}'...")
        read_result = await resource_manager.read_resource(test_uri)
        print(f"✅ Read resource successfully:")
        for content in read_result.contents:
            print(f"   URI: {content['uri']}")
            print(f"   MIME Type: {content['mimeType']}")
            print(f"   Content: {content['text'][:50]}...")
        
        # Test 4: Update resource
        print(f"\n✏️  Test 4: Updating resource...")
        updated = await resource_manager.update_resource(
            uri=test_uri,
            description="Updated description for test resource",
            content="Updated content for the MCP resource handler."
        )
        print(f"✅ Updated resource: {updated.description}")
        
        # Test 5: Search resources
        print(f"\n🔍 Test 5: Searching resources...")
        search_results = await resource_manager.search_resources("test")
        print(f"✅ Found {len(search_results)} resources matching 'test'")
        
        # Test 6: Get resource count
        print(f"\n🔢 Test 6: Counting resources...")
        count = await resource_manager.get_resource_count()
        print(f"✅ Total resources in database: {count}")
        
        # Test 7: Delete resource
        print(f"\n🗑️  Test 7: Deleting test resource...")
        deleted = await resource_manager.delete_resource(test_uri)
        print(f"✅ Deleted resource: {deleted}")
        
        # Verify deletion
        final_count = await resource_manager.get_resource_count()
        print(f"✅ Resources after deletion: {final_count}")
        
        print("\n" + "=" * 50)
        print("🎉 All resource manager tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Disconnect
        await db_manager.disconnect()
        print("🔌 Database connections closed")
    
    return True


async def main():
    """Main test function."""
    # Check if MongoDB URL is set
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("❌ MONGODB_URL environment variable not set")
        print("Please set your MongoDB Atlas connection string:")
        print("export MONGODB_URL='mongodb+srv://username:password@cluster.mongodb.net/'")
        return False
    
    print(f"📡 Using MongoDB URL: {mongodb_url[:20]}...")
    print()
    
    # Run tests
    success = await test_resource_operations()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("\n📝 Next steps:")
        print("1. MCP resource handlers are ready")
        print("2. Create REST API endpoints")
        print("3. Integrate with frontend UI")
    else:
        print("\n❌ Some tests failed. Please check the logs.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
