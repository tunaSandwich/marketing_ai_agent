#!/bin/bash
# Setup script for RAG system

echo "🔧 Setting up RAG system..."

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if index exists
if [ ! -d "brands/goodpods/index" ]; then
    echo "📚 Indexing knowledge base (first time setup)..."
    python scripts/index_brand_knowledge.py goodpods
    
    if [ $? -eq 0 ]; then
        echo "✅ Knowledge base indexed successfully!"
    else
        echo "❌ Failed to index knowledge base"
        exit 1
    fi
else
    echo "✅ Knowledge base already indexed"
fi

echo ""
echo "🎯 RAG system ready! You can now run:"
echo "  python scripts/demo_discovery.py        # Full demo with RAG"
echo "  python scripts/test_rag.py             # Test RAG retrieval"
echo "  python scripts/demo_rag_enhanced.py    # Show RAG enhancements"
echo ""
echo "💡 Remember to activate the virtual environment first:"
echo "  source .venv/bin/activate"