#!/usr/bin/env python3
"""
Populate Redis suggestions index from existing MongoDB resources.

This script reads all existing resources and their chunks from MongoDB
and populates the Redis suggestions index with searchable terms.

Run after implementing the suggestions feature to backfill data.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from motor.motor_asyncio import AsyncIOMotorClient
from ai_mcp_toolkit.services.suggestion_service import SuggestionService


async def populate_suggestions():
    """Populate Redis suggestions from all existing resources."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb+srv://mcp_toolkit_user:54eahEzxCWw8GFB1@ai-mcp-toolkit.va8qnkw.mongodb.net/')
    db = client.ai_mcp_toolkit
    
    print("🔍 Reading existing resources from MongoDB...")
    
    # Get all resources
    resources = await db.resources.find({}).to_list(None)
    total_resources = len(resources)
    
    print(f"📊 Found {total_resources} resources to index\n")
    
    if total_resources == 0:
        print("✅ No resources to index")
        return
    
    # Initialize suggestion service
    suggestion_service = SuggestionService()
    
    # Process each resource
    indexed_count = 0
    error_count = 0
    
    for i, resource in enumerate(resources, 1):
        try:
            resource_id = str(resource['_id'])
            file_name = resource.get('file_name', 'unknown')
            company_id = resource.get('company_id')
            
            # Get chunks for this resource
            chunks = await db.resource_chunks.find({
                'parent_id': resource_id
            }).to_list(None)
            
            # Combine all chunk text
            combined_content = ' '.join(
                chunk.get('text', '') for chunk in chunks if chunk.get('text')
            )
            
            # Index terms in Redis
            await suggestion_service.add_document_terms(
                file_name=file_name,
                entities=resource.get('entities', []),
                keywords=resource.get('keywords', []),
                vendor=resource.get('vendor'),
                content=combined_content,
                company_id=company_id
            )
            
            indexed_count += 1
            
            # Progress update every 10 resources
            if indexed_count % 10 == 0:
                print(f"  ✅ Indexed {indexed_count}/{total_resources} resources...")
            
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error indexing resource {resource.get('file_name', 'unknown')}: {e}")
    
    print(f"\n✅ Population complete!")
    print(f"  📝 Indexed: {indexed_count}")
    print(f"  ❌ Errors: {error_count}")
    
    # Verify by checking a sample
    print(f"\n🔍 Verifying suggestions index...")
    
    # Get unique company IDs
    company_ids = list(set(r.get('company_id') for r in resources if r.get('company_id')))
    
    for company_id in company_ids[:3]:  # Check first 3 companies
        suggestions = await suggestion_service.get_suggestions(
            query="",  # Empty query to see if any data exists
            company_id=company_id,
            limit=5
        )
        
        if suggestions:
            print(f"  ✅ Company {company_id[:8]}...: Found suggestions")
        else:
            # Try with a common letter
            test_suggestions = await suggestion_service.get_suggestions(
                query="g",
                company_id=company_id,
                limit=5
            )
            if test_suggestions:
                print(f"  ✅ Company {company_id[:8]}...: {len(test_suggestions)} suggestions for 'g'")
                for s in test_suggestions[:3]:
                    print(f"      - {s['text']} ({s['type']})")
            else:
                print(f"  ⚠️  Company {company_id[:8]}...: No suggestions found")


if __name__ == "__main__":
    asyncio.run(populate_suggestions())
