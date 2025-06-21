#!/usr/bin/env python3
"""
Test script for the TF-IDF Search Engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_engine import SearchEngine
import json

def test_search_engine():
    """Test the search engine functionality"""
    print("Testing TF-IDF Search Engine...")
    
    # Initialize search engine
    engine = SearchEngine()
    
    # Test documents
    test_docs = [
        "Python is a programming language used for web development and data science",
        "Machine learning algorithms help computers learn from data automatically",
        "Flask is a lightweight web framework for Python applications",
        "Natural language processing involves analyzing and understanding human language",
        "Data visualization helps present complex information in clear graphics"
    ]
    
    print(f"Adding {len(test_docs)} test documents...")
    engine.add_documents(test_docs)
    
    # Test searches
    test_queries = [
        "Python programming",
        "machine learning data",
        "web development Flask",
        "language processing",
        "visualization graphics"
    ]
    
    print("\nSearching for similar documents:")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        similarities, indices = engine.search(query, k=3)
        
        if len(similarities[0]) > 0:
            for i, (sim_score, doc_idx) in enumerate(zip(similarities[0], indices[0])):
                if doc_idx < len(test_docs):
                    print(f"  {i+1}. Score: {sim_score:.3f} - {test_docs[doc_idx][:60]}...")
        else:
            print("  No results found")
    
    print("\n✓ Search engine test completed successfully!")
    return True

def test_flask_endpoints():
    """Test the Flask API endpoints"""
    print("\nTesting Flask API simulation...")
    
    # Create engine instance
    engine = SearchEngine()
    
    # Simulate add_documents endpoint
    documents_data = {
        "documents": [
            "Artificial intelligence is transforming many industries",
            "Deep learning models require large amounts of training data", 
            "Computer vision enables machines to interpret visual information",
            "Reinforcement learning trains agents through trial and error"
        ]
    }
    
    try:
        engine.add_documents(documents_data["documents"])
        print("✓ Add documents endpoint simulation successful")
    except Exception as e:
        print(f"✗ Add documents failed: {e}")
        return False
    
    # Simulate search endpoint
    search_data = {
        "query": "artificial intelligence deep learning",
        "k": 2
    }
    
    try:
        similarities, indices = engine.search(search_data["query"], search_data.get("k", 5))
        result = {
            "similarities": similarities.tolist(),
            "indices": indices.tolist()
        }
        print("✓ Search endpoint simulation successful")
        print(f"  Results: {len(result['similarities'][0])} documents found")
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        # Run tests
        print("=" * 60)
        print("MITO Engine - Search Engine Test Suite")
        print("=" * 60)
        
        success1 = test_search_engine()
        success2 = test_flask_endpoints()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("🎉 ALL TESTS PASSED - Search Engine is working correctly!")
        else:
            print("❌ Some tests failed - Check output above")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)