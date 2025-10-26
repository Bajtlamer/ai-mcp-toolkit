#!/usr/bin/env python3
"""Direct test script to verify database connections without package imports."""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import modules directly
from ai_mcp_toolkit.models.database import DatabaseManager
from ai_mcp_toolkit.models.documents import Resource, ResourceType


async def test_database_connection():
    """Test database connections."""
    print("🔍 Testing database connections...")
    
    try:
        # Create a new database manager instance
        db_manager = DatabaseManager()
        
        # Connect to databases
        await db_manager.connect()
        print("✅ Database connections established successfully")
        
        # Test MongoDB connection
        health = await db_manager.health_check()
        print(f"📊 Health check results: {health}")
        
        if health["overall"]:
            print("✅ All database connections are healthy")
            
            # Test creating a simple resource
            test_resource = Resource(
                uri="test://example.com/test.txt",
                name="Test Resource",
                description="A test resource for verification",
                mime_type="text/plain",
                resource_type=ResourceType.TEXT,
                content="This is a test resource content."
            )
            
            # Save to database
            await test_resource.save()
            print("✅ Successfully created and saved test resource")
            
            # Retrieve from database
            retrieved_resource = await Resource.find_one(Resource.uri == "test://example.com/test.txt")
            if retrieved_resource:
                print(f"✅ Successfully retrieved resource: {retrieved_resource.name}")
            else:
                print("❌ Failed to retrieve resource")
            
            # Clean up test resource
            await test_resource.delete()
            print("✅ Cleaned up test resource")
            
        else:
            print("❌ Database health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
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
    print("🚀 AI MCP Toolkit Database Test")
    print("=" * 50)
    
    # Check if MongoDB URL is set
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("❌ MONGODB_URL environment variable not set")
        print("Please set your MongoDB Atlas connection string:")
        print("export MONGODB_URL='mongodb+srv://username:password@cluster.mongodb.net/'")
        return False
    
    print(f"📡 Using MongoDB URL: {mongodb_url[:20]}...")
    
    # Run the test
    success = await test_database_connection()
    
    if success:
        print("\n🎉 All tests passed! Database setup is working correctly.")
        print("\nNext steps:")
        print("1. Database layer is ready for MCP protocol implementation")
        print("2. Start implementing the MCP resource handlers")
        print("3. Begin Phase 1 tasks from the enhancement plan")
    else:
        print("\n❌ Database test failed. Please check your configuration.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
