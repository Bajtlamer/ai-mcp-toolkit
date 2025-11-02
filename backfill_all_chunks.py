#!/usr/bin/env python3
"""
Backfill script to populate normalized searchable fields for ALL existing chunks.
This adds searchable_text, text_normalized, and ocr_text_normalized fields.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from motor.motor_asyncio import AsyncIOMotorClient
from ai_mcp_toolkit.utils.text_normalizer import normalize_text


async def backfill_chunks():
    """Backfill normalized searchable fields for all chunks."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb+srv://mcp_toolkit_user:54eahEzxCWw8GFB1@ai-mcp-toolkit.va8qnkw.mongodb.net/')
    db = client.ai_mcp_toolkit
    
    print("🔍 Checking existing chunks...")
    
    # Get total count
    total_chunks = await db.resource_chunks.count_documents({})
    print(f"📊 Total chunks in database: {total_chunks}")
    
    # Count chunks missing searchable_text
    missing_searchable = await db.resource_chunks.count_documents({
        "$or": [
            {"searchable_text": {"$exists": False}},
            {"searchable_text": None},
            {"searchable_text": ""}
        ]
    })
    print(f"⚠️  Chunks missing searchable_text: {missing_searchable}")
    
    if missing_searchable == 0:
        print("✅ All chunks already have searchable_text!")
        return
    
    # Process all chunks
    print(f"\n🚀 Processing {missing_searchable} chunks...")
    updated_count = 0
    error_count = 0
    
    # Fetch chunks in batches
    batch_size = 100
    skip = 0
    
    while True:
        chunks = await db.resource_chunks.find({
            "$or": [
                {"searchable_text": {"$exists": False}},
                {"searchable_text": None},
                {"searchable_text": ""}
            ]
        }).skip(skip).limit(batch_size).to_list(batch_size)
        
        if not chunks:
            break
        
        for chunk in chunks:
            try:
                chunk_id = chunk['_id']
                
                # Extract text fields
                text = chunk.get('text', '') or ''
                ocr_text = chunk.get('ocr_text', '') or ''
                image_description = chunk.get('image_description', '') or ''
                
                # Build searchable text (combine all text sources)
                searchable_parts = []
                if text:
                    searchable_parts.append(text)
                if ocr_text:
                    searchable_parts.append(ocr_text)
                if image_description:
                    searchable_parts.append(image_description)
                
                searchable_text = ' '.join(searchable_parts).strip()
                
                # Normalize all text fields
                text_normalized = normalize_text(text) if text else None
                ocr_text_normalized = normalize_text(ocr_text) if ocr_text else None
                searchable_text_normalized = normalize_text(searchable_text) if searchable_text else None
                
                # Update chunk with normalized fields
                update_data = {
                    "searchable_text": searchable_text_normalized,
                    "text_normalized": text_normalized,
                    "ocr_text_normalized": ocr_text_normalized
                }
                
                await db.resource_chunks.update_one(
                    {"_id": chunk_id},
                    {"$set": update_data}
                )
                
                updated_count += 1
                
                # Log progress every 50 chunks
                if updated_count % 50 == 0:
                    print(f"  ✅ Updated {updated_count}/{missing_searchable} chunks...")
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ Error processing chunk {chunk.get('_id')}: {e}")
        
        skip += batch_size
    
    print(f"\n✅ Backfill complete!")
    print(f"  📝 Updated: {updated_count}")
    print(f"  ❌ Errors: {error_count}")
    
    # Verify
    remaining = await db.resource_chunks.count_documents({
        "$or": [
            {"searchable_text": {"$exists": False}},
            {"searchable_text": None},
            {"searchable_text": ""}
        ]
    })
    print(f"  ⚠️  Remaining without searchable_text: {remaining}")


if __name__ == "__main__":
    asyncio.run(backfill_chunks())
