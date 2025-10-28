"""Test script for embedding manager functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_mcp_toolkit.managers.embedding_manager import get_embedding_manager


async def test_single_embedding():
    """Test generating a single embedding."""
    print("=" * 60)
    print("TEST 1: Single Embedding Generation")
    print("=" * 60)
    
    manager = get_embedding_manager(provider="ollama")
    
    text = "This is a test document about artificial intelligence and machine learning."
    
    print(f"\nText: {text}")
    print(f"Provider: {manager.provider}")
    print(f"Model: {manager.model}")
    print(f"Expected dimensions: {manager.dimensions}")
    
    print("\nGenerating embedding...")
    embedding = await manager.generate_embedding(text)
    
    print(f"✅ Embedding generated!")
    print(f"Dimensions: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"Sample (truncated): [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")
    
    assert len(embedding) == manager.dimensions, f"Expected {manager.dimensions} dims, got {len(embedding)}"
    print("✅ Dimension check passed!")


async def test_batch_embeddings():
    """Test batch embedding generation."""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Embedding Generation")
    print("=" * 60)
    
    manager = get_embedding_manager(provider="ollama")
    
    texts = [
        "Artificial intelligence is transforming technology.",
        "Machine learning models can process vast amounts of data.",
        "Neural networks are inspired by biological neurons.",
    ]
    
    print(f"\nGenerating embeddings for {len(texts)} texts...")
    for i, text in enumerate(texts):
        print(f"  {i+1}. {text}")
    
    embeddings = await manager.generate_batch_embeddings(texts)
    
    print(f"\n✅ Generated {len(embeddings)} embeddings!")
    for i, emb in enumerate(embeddings):
        print(f"  Text {i+1}: {len(emb)} dimensions")
    
    assert len(embeddings) == len(texts), f"Expected {len(texts)} embeddings, got {len(embeddings)}"
    print("✅ Batch generation successful!")


async def test_chunking():
    """Test text chunking."""
    print("\n" + "=" * 60)
    print("TEST 3: Text Chunking")
    print("=" * 60)
    
    manager = get_embedding_manager(provider="ollama")
    
    # Create a long text
    long_text = " ".join([
        f"This is sentence number {i} in a long document about various topics."
        for i in range(100)
    ])
    
    print(f"\nOriginal text length: {len(long_text)} characters")
    
    chunks = manager.chunk_text(long_text, chunk_size=500, overlap=100)
    
    print(f"✅ Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"\nChunk {i+1}:")
        print(f"  Index: {chunk['index']}")
        print(f"  Char range: {chunk['char_start']} - {chunk['char_end']}")
        print(f"  Length: {len(chunk['text'])} chars")
        print(f"  Preview: {chunk['text'][:80]}...")
    
    if len(chunks) > 3:
        print(f"\n  ... and {len(chunks) - 3} more chunks")
    
    assert len(chunks) > 0, "Expected at least one chunk"
    print("\n✅ Chunking successful!")


async def test_document_embedding():
    """Test full document embedding with chunking."""
    print("\n" + "=" * 60)
    print("TEST 4: Document Embedding (Short)")
    print("=" * 60)
    
    manager = get_embedding_manager(provider="ollama")
    
    short_text = "This is a short document that doesn't need chunking."
    
    print(f"\nShort document ({len(short_text)} chars)")
    result = await manager.embed_document(short_text, chunk_if_large=True, chunk_size=1000)
    
    print(f"✅ Embeddings: {len(result['embeddings'])} dimensions")
    print(f"Chunks: {result['chunk_count']}")
    print(f"Chunked: {'Yes' if result['chunks'] else 'No'}")
    
    assert result['chunk_count'] == 0, "Short doc shouldn't be chunked"
    assert len(result['embeddings']) == manager.dimensions
    print("✅ Short document test passed!")
    
    print("\n" + "=" * 60)
    print("TEST 5: Document Embedding (Long)")
    print("=" * 60)
    
    long_text = " ".join([
        f"Paragraph {i}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        f"This is part of a much longer document that will require chunking."
        for i in range(50)
    ])
    
    print(f"\nLong document ({len(long_text)} chars)")
    result = await manager.embed_document(long_text, chunk_if_large=True, chunk_size=1000)
    
    print(f"✅ Embeddings: {len(result['embeddings'])} dimensions")
    print(f"Chunks: {result['chunk_count']}")
    print(f"Chunked: {'Yes' if result['chunks'] else 'No'}")
    
    if result['chunks']:
        print(f"\nChunk details:")
        for i, chunk in enumerate(result['chunks'][:3]):
            print(f"  Chunk {i+1}: {len(chunk['embeddings'])} dims, {len(chunk['text'])} chars")
    
    assert result['chunk_count'] > 0, "Long doc should be chunked"
    assert result['chunks'] is not None
    print("✅ Long document test passed!")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EMBEDDING MANAGER TEST SUITE")
    print("=" * 60)
    
    try:
        await test_single_embedding()
        await test_batch_embeddings()
        await test_chunking()
        await test_document_embedding()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
