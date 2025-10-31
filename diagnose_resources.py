#!/usr/bin/env python3
"""Diagnostic script to inspect resource storage in MongoDB."""

import asyncio
import sys
import os
from bson import ObjectId
import json
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Import from the project
from src.ai_mcp_toolkit.models.documents import Resource, ResourceChunk, User, Conversation


async def inspect_resource(resource_id: str):
    """Inspect a specific resource."""
    try:
        # Find resource
        resource = await Resource.get(ObjectId(resource_id))
        
        if not resource:
            print(f"Resource {resource_id} not found")
            return
        
        print("=" * 80)
        print(f"RESOURCE: {resource_id}")
        print("=" * 80)
        
        # Show all fields
        data = {
            "_id": str(resource.id),
            "uri": resource.uri,
            "name": resource.name,
            "description": resource.description,
            "mime_type": resource.mime_type,
            "resource_type": resource.resource_type,
            "owner_id": resource.owner_id,
            "file_id": resource.file_id,
            "file_name": resource.file_name,
            "file_type": resource.file_type,
            "company_id": resource.company_id,
            "size_bytes": resource.size_bytes,
            "tags": resource.tags,
            "vendor": resource.vendor,
            "currency": resource.currency,
            "amounts_cents": resource.amounts_cents,
            "entities": resource.entities,
            "keywords": resource.keywords,
            "dates": resource.dates,
            "summary": resource.summary[:200] + "..." if resource.summary and len(resource.summary) > 200 else resource.summary,
            "content": resource.content[:200] + "..." if resource.content and len(resource.content) > 200 else resource.content,
            "text_embedding": f"[{len(resource.text_embedding)} dimensions]" if resource.text_embedding else None,
            "image_embedding": f"[{len(resource.image_embedding)} dimensions]" if resource.image_embedding else None,
            "metadata": resource.metadata,
            "created_at": str(resource.created_at),
        }
        
        print(json.dumps(data, indent=2, default=str))
        
        # Count chunks
        chunks = await ResourceChunk.find(ResourceChunk.parent_id == str(resource.id)).to_list()
        print(f"\n{'=' * 80}")
        print(f"CHUNKS: {len(chunks)} total")
        print(f"{'=' * 80}")
        
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\nChunk {i+1}:")
            print(f"  - chunk_type: {chunk.chunk_type}")
            print(f"  - chunk_index: {chunk.chunk_index}")
            print(f"  - text: {chunk.text[:100]}..." if chunk.text and len(chunk.text) > 100 else f"  - text: {chunk.text}")
            print(f"  - text_embedding: [{len(chunk.text_embedding)} dimensions]" if chunk.text_embedding else "  - text_embedding: None")
        
        if len(chunks) > 3:
            print(f"\n... and {len(chunks) - 3} more chunks")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


async def list_recent_resources():
    """List most recent resources."""
    try:
        resources = await Resource.find().sort("-created_at").limit(5).to_list()
        
        print("=" * 80)
        print("RECENT RESOURCES")
        print("=" * 80)
        
        for resource in resources:
            print(f"\nID: {resource.id}")
            print(f"  name: {resource.name}")
            print(f"  file_name: {resource.file_name}")
            print(f"  file_type: {resource.file_type}")
            print(f"  mime_type: {resource.mime_type}")
            print(f"  has_text_embedding: {resource.text_embedding is not None}")
            print(f"  has_content: {resource.content is not None}")
            print(f"  created_at: {resource.created_at}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point."""
    # Initialize database connection (use same env var as server)
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "ai_mcp_toolkit")
    
    print(f"Connecting to: {mongodb_url[:50]}... (database: {db_name})")
    
    client = AsyncIOMotorClient(mongodb_url)
    database = client[db_name]
    
    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[User, Conversation, Resource, ResourceChunk]
    )
    
    print("Connected successfully!\n")
    
    if len(sys.argv) > 1:
        # Inspect specific resource
        resource_id = sys.argv[1]
        await inspect_resource(resource_id)
    else:
        # List recent resources
        await list_recent_resources()


if __name__ == "__main__":
    asyncio.run(main())
