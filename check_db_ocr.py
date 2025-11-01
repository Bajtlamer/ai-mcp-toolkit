#!/usr/bin/env python3
"""Check if OCR text is actually in the database for article.jpg"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment
os.environ.setdefault("LOG_LEVEL", "INFO")

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


async def main():
    # Get MongoDB connection string from environment or use default
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
    
    if not mongo_uri:
        print("ERROR: MONGODB_URI not set in environment")
        print("\nTry:")
        print("  export MONGODB_URI='your_connection_string'")
        print("  python check_db_ocr.py")
        return
    
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.ai_mcp_toolkit
    
    # Find article.jpg
    print("\nSearching for article.jpg...")
    resource = await db.resources.find_one(
        {"file_name": {"$regex": "article", "$options": "i"}},
        sort=[("_id", -1)]  # Get most recent
    )
    
    if not resource:
        print("❌ article.jpg not found in database")
        return
    
    print(f"\n{'='*70}")
    print(f"RESOURCE: {resource['file_name']}")
    print(f"{'='*70}")
    print(f"ID: {resource['_id']}")
    print(f"Type: {resource.get('file_type')}")
    print(f"OCR at resource level: {bool(resource.get('ocr_text'))}")
    if resource.get('ocr_text'):
        print(f"  Preview: {resource['ocr_text'][:100]}...")
    
    # Find chunks
    print(f"\n{'='*70}")
    print("CHUNKS")
    print(f"{'='*70}")
    
    chunks = await db.resource_chunks.find(
        {"parent_id": str(resource['_id'])}
    ).to_list(10)
    
    print(f"Found {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Chunk {i} ---")
        print(f"  ID: {chunk['_id']}")
        print(f"  Type: {chunk.get('chunk_type', 'N/A')}")
        
        # Check text field
        text = chunk.get('text', '')
        print(f"  text field: {len(text)} chars")
        if text:
            print(f"    Preview: {text[:80]}...")
        
        # Check OCR field
        ocr = chunk.get('ocr_text', '')
        print(f"  ocr_text field: {len(ocr) if ocr else 0} chars")
        if ocr:
            print(f"    Preview: {ocr[:80]}...")
            print(f"    🔍 Contains 'Jak se formuje': {'Jak se formuje' in ocr}")
            print(f"    🔍 Contains 'datová': {'datová' in ocr}")
            print(f"    🔍 Contains 'budoucnost': {'budoucnost' in ocr}")
        
        # Check caption
        caption = chunk.get('caption')
        print(f"  caption: {caption[:80] if caption else 'None'}...")
        
        # Check embeddings
        print(f"  text_embedding: {bool(chunk.get('text_embedding'))}")
        print(f"  caption_embedding: {bool(chunk.get('caption_embedding'))}")
        
        print()
    
    # Now search using compound search
    print(f"{'='*70}")
    print("TESTING COMPOUND SEARCH")
    print(f"{'='*70}")
    
    query = "Jak se formuje datová budoucnost"
    print(f"Query: '{query}'")
    
    # Try to mimic what the search does
    pipeline = [
        {
            "$search": {
                "index": "resource_chunks_compound",
                "text": {
                    "query": query,
                    "path": ["ocr_text", "text", "caption"]
                }
            }
        },
        {"$limit": 5},
        {
            "$project": {
                "file_name": 1,
                "text": 1,
                "ocr_text": 1,
                "score": {"$meta": "searchScore"}
            }
        }
    ]
    
    try:
        print("\nExecuting Atlas text search on ocr_text field...")
        results = await db.resource_chunks.aggregate(pipeline).to_list(5)
        
        if results:
            print(f"✅ Found {len(results)} results!")
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i}:")
                print(f"    File: {result.get('file_name')}")
                print(f"    Score: {result.get('score', 0):.4f}")
                ocr = result.get('ocr_text', '')
                if ocr:
                    print(f"    OCR length: {len(ocr)}")
                    print(f"    OCR preview: {ocr[:100]}...")
        else:
            print("❌ No results from Atlas search")
            print("\nPossible reasons:")
            print("  1. Atlas index not ready")
            print("  2. OCR text not indexed")
            print("  3. Wrong index name")
            
    except Exception as e:
        print(f"❌ Atlas search failed: {e}")
        print("\nThis means Atlas search is not working!")
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    has_ocr_in_chunks = any(c.get('ocr_text') for c in chunks)
    
    if not chunks:
        print("❌ No chunks found - ingestion failed")
    elif not has_ocr_in_chunks:
        print("❌ Chunks exist but no OCR text - extraction/storage failed")
    else:
        print("✅ OCR text is in database")
        print("\nIf search still doesn't work, the problem is:")
        print("  - Atlas compound search is failing (check backend logs)")
        print("  - Or falling back to legacy search (doesn't search ocr_text)")


if __name__ == "__main__":
    asyncio.run(main())
