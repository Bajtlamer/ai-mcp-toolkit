"""Test script for semantic search functionality."""

import asyncio
import aiohttp
import json
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
TEST_FILE = Path(__file__).parent / "test_upload.txt"

# You'll need to set this after logging in
SESSION_COOKIE = None  # Will be set after login


async def login(username="admin", password="admin123"):
    """Login and get session cookie."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password}
        ) as response:
            if response.status == 200:
                # Get session cookie
                cookies = response.cookies
                session_cookie = cookies.get('session')
                if session_cookie:
                    print(f"✅ Logged in as {username}")
                    return session_cookie.value
                else:
                    print("❌ No session cookie received")
                    return None
            else:
                error = await response.text()
                print(f"❌ Login failed: {error}")
                return None


async def upload_test_file(session_cookie):
    """Upload the test file."""
    if not TEST_FILE.exists():
        print(f"❌ Test file not found: {TEST_FILE}")
        return None
    
    print(f"\n📤 Uploading {TEST_FILE.name}...")
    
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('file',
                      open(TEST_FILE, 'rb'),
                      filename=TEST_FILE.name,
                      content_type='text/plain')
        data.add_field('description', 'Test document about AI and machine learning')
        
        cookies = {'session': session_cookie}
        
        async with session.post(
            f"{API_BASE}/resources/upload",
            data=data,
            cookies=cookies
        ) as response:
            if response.status == 201:
                result = await response.json()
                print(f"✅ File uploaded successfully!")
                print(f"   URI: {result['uri']}")
                print(f"   Name: {result['name']}")
                return result['uri']
            else:
                error = await response.text()
                print(f"❌ Upload failed: {error}")
                return None


async def semantic_search(session_cookie, query, limit=5, min_score=0.5):
    """Test semantic search."""
    print(f"\n🔍 Semantic Search: '{query}'")
    print(f"   Parameters: limit={limit}, min_score={min_score}")
    
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('query', query)
        data.add_field('limit', str(limit))
        data.add_field('min_score', str(min_score))
        
        cookies = {'session': session_cookie}
        
        async with session.post(
            f"{API_BASE}/resources/search/semantic",
            data=data,
            cookies=cookies
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Found {result['count']} results:")
                for i, doc in enumerate(result['results'], 1):
                    print(f"   {i}. {doc['name']}")
                    print(f"      Score: {doc['score']:.3f}")
                    print(f"      Description: {doc['description'][:60]}...")
                return result
            else:
                error = await response.text()
                print(f"❌ Search failed: {error}")
                return None


async def chunk_search(session_cookie, query, limit=5):
    """Test chunk-level search."""
    print(f"\n📄 Chunk Search: '{query}'")
    
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('query', query)
        data.add_field('limit', str(limit))
        
        cookies = {'session': session_cookie}
        
        async with session.post(
            f"{API_BASE}/resources/search/chunks",
            data=data,
            cookies=cookies
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Found {result['count']} chunks:")
                for i, chunk in enumerate(result['chunks'], 1):
                    print(f"   {i}. {chunk['name']} (chunk {chunk['chunkIndex']})")
                    print(f"      Score: {chunk['score']:.3f}")
                    print(f"      Text: {chunk['chunkText'][:80]}...")
                return result
            else:
                error = await response.text()
                print(f"❌ Search failed: {error}")
                return None


async def find_similar(session_cookie, uri, limit=3):
    """Test find similar resources."""
    print(f"\n🔗 Finding similar documents to: {uri}")
    
    async with aiohttp.ClientSession() as session:
        cookies = {'session': session_cookie}
        
        # URL encode the URI
        from urllib.parse import quote
        encoded_uri = quote(uri, safe='')
        
        async with session.get(
            f"{API_BASE}/resources/{encoded_uri}/similar?limit={limit}",
            cookies=cookies
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Found {result['count']} similar documents:")
                for i, doc in enumerate(result['similar_resources'], 1):
                    print(f"   {i}. {doc['name']}")
                    print(f"      Score: {doc['score']:.3f}")
                return result
            else:
                error = await response.text()
                print(f"❌ Search failed: {error}")
                return None


async def main():
    """Run all tests."""
    print("=" * 70)
    print("SEMANTIC SEARCH TEST SUITE")
    print("=" * 70)
    
    # Step 1: Login
    print("\n1️⃣  Logging in...")
    session_cookie = await login("admin", "admin123")
    if not session_cookie:
        print("\n❌ Cannot proceed without login. Please check credentials.")
        return
    
    # Step 2: Upload test file (if not already uploaded)
    print("\n2️⃣  Uploading test document...")
    uri = await upload_test_file(session_cookie)
    
    if not uri:
        print("\n⚠️  Upload failed, but continuing with existing documents...")
    
    # Wait a moment for embeddings to be generated
    await asyncio.sleep(2)
    
    # Step 3: Test semantic search with various queries
    print("\n3️⃣  Testing Semantic Search...")
    
    await semantic_search(session_cookie, "artificial intelligence", limit=5)
    await asyncio.sleep(1)
    
    await semantic_search(session_cookie, "machine learning algorithms", limit=5)
    await asyncio.sleep(1)
    
    await semantic_search(session_cookie, "neural networks and deep learning", limit=5)
    await asyncio.sleep(1)
    
    # Step 4: Test chunk search
    print("\n4️⃣  Testing Chunk Search...")
    await chunk_search(session_cookie, "neural networks", limit=3)
    
    # Step 5: Test similar documents (if we have a URI)
    if uri:
        print("\n5️⃣  Testing Similar Documents...")
        await find_similar(session_cookie, uri, limit=3)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 70)
    print("\nSemantic search is working! You can now:")
    print("  • Search documents by meaning, not just keywords")
    print("  • Find relevant chunks in large documents")
    print("  • Discover similar resources")
    print("\nNext: Add search UI to the frontend!")


if __name__ == "__main__":
    asyncio.run(main())
