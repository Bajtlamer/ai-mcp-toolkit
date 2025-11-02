#!/usr/bin/env python3
"""
Backfill script to add normalized text fields to existing article.jpg chunks.
Run this to update article.jpg without re-uploading.
"""

import asyncio
import unicodedata
import re
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient


# Standalone text normalizer functions
def normalize_text(text, lowercase=True):
    """Normalize text by removing diacritics."""
    if not text:
        return text
    
    # Normalize to NFD and remove combining characters
    nfd = unicodedata.normalize('NFD', text)
    without_diacritics = ''.join(
        char for char in nfd 
        if unicodedata.category(char) != 'Mn'
    )
    
    # Normalize back to NFC
    normalized = unicodedata.normalize('NFC', without_diacritics)
    
    if lowercase:
        normalized = normalized.lower()
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()


def create_searchable_text(*text_parts, separator=" "):
    """Create searchable text from multiple sources."""
    valid_parts = [part for part in text_parts if part]
    if not valid_parts:
        return ""
    combined = separator.join(valid_parts)
    return normalize_text(combined, lowercase=True)


def tokenize_for_search(text):
    """Tokenize text into search terms."""
    if not text:
        return []
    normalized = normalize_text(text)
    tokens = re.split(r'[\s\-_.,;:!?(){}[\]<>/"\']+', normalized)
    return [t for t in tokens if len(t) >= 2]


async def backfill_article_jpg():
    """Add normalized fields to article.jpg chunks."""
    
    # Get MongoDB URI from environment or use default
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    print(f"📡 Connecting to MongoDB...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_uri)
    db = client.ai_mcp_toolkit
    
    print("🔍 Finding article.jpg...")
    
    # Find article.jpg using raw MongoDB query
    resource = await db.resources.find_one({"file_name": "article.jpg"})
    if not resource:
        print("❌ article.jpg NOT FOUND!")
        return
    
    resource_id = str(resource["_id"])
    print(f"✅ Found article.jpg: {resource_id}")
    
    # Find its chunks
    chunks = await db.resource_chunks.find({"parent_id": resource_id}).to_list(length=100)
    
    if not chunks:
        print("❌ NO CHUNKS found!")
        return
    
    print(f"✅ Found {len(chunks)} chunks")
    
    # Update each chunk
    for i, chunk in enumerate(chunks):
        print(f"\n📝 Processing chunk {i}...")
        
        # Get original text
        text = chunk.get("text", "")
        ocr_text = chunk.get("ocr_text", "")
        caption = chunk.get("caption", "")
        image_labels = chunk.get("image_labels", [])
        
        print(f"   Original text: {len(text)} chars")
        print(f"   OCR text: {len(ocr_text)} chars")
        print(f"   Caption: {len(caption)} chars")
        
        # Normalize text
        text_normalized = normalize_text(text) if text else None
        ocr_text_normalized = normalize_text(ocr_text) if ocr_text else None
        image_description = caption  # Use caption as image description
        
        # Create searchable text
        searchable_text = create_searchable_text(
            text,
            ocr_text,
            caption,
            ' '.join(image_labels)
        )
        
        # Extract keywords
        keywords = tokenize_for_search(searchable_text) if searchable_text else []
        existing_keywords = chunk.get("keywords", [])
        all_keywords = list(set(existing_keywords + keywords))
        
        print(f"   ✨ Normalized text: {len(text_normalized or '')} chars")
        print(f"   ✨ Normalized OCR: {len(ocr_text_normalized or '')} chars")
        print(f"   ✨ Searchable text: {len(searchable_text or '')} chars")
        print(f"   ✨ Keywords: {len(all_keywords)}")
        
        if searchable_text:
            print(f"   Preview: '{searchable_text[:100]}...'")
        
        # Update chunk in database
        await db.resource_chunks.update_one(
            {"_id": chunk["_id"]},
            {"$set": {
                "text_normalized": text_normalized,
                "ocr_text_normalized": ocr_text_normalized,
                "searchable_text": searchable_text,
                "image_description": image_description,
                "keywords": all_keywords
            }}
        )
        print(f"   ✅ Chunk {i} updated!")
    
    print(f"\n🎉 Successfully backfilled {len(chunks)} chunks for article.jpg!")
    print(f"\n🔍 Now search for: 'Jak se formuje datová budoucnost'")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use MongoDB URI from command line
        os.environ["MONGODB_URI"] = sys.argv[1]
        print(f"✨ Using MongoDB URI from command line")
    elif not os.getenv("MONGODB_URI"):
        print("⚠️  MongoDB URI not provided!")
        print("")
        print("Usage:")
        print("  python3 backfill_article_jpg.py 'mongodb+srv://user:pass@cluster.mongodb.net'")
        print("  OR set MONGODB_URI environment variable")
        print("")
        sys.exit(1)
    
    asyncio.run(backfill_article_jpg())
