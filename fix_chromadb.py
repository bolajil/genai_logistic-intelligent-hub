"""Fix ChromaDB dimension mismatch by resetting the problematic collection."""
import chromadb
from pathlib import Path

# ChromaDB path from config
chroma_path = Path("data/chromadb")

print("Fixing ChromaDB dimension mismatch...")
print(f"ChromaDB path: {chroma_path}")

try:
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=str(chroma_path))
    
    # List all collections
    collections = client.list_collections()
    print(f"\nFound {len(collections)} collections:")
    for coll in collections:
        print(f"  - {coll.name}")
    
    # Delete query_trials if it exists
    try:
        client.delete_collection("query_trials")
        print("\n✅ Deleted 'query_trials' collection")
    except Exception as e:
        print(f"\n⚠️ Could not delete 'query_trials': {e}")
    
    # List collections after deletion
    collections = client.list_collections()
    print(f"\nRemaining collections: {len(collections)}")
    for coll in collections:
        print(f"  - {coll.name}")
    
    print("\n✅ ChromaDB fixed!")
    print("\nNext steps:")
    print("1. Refresh your browser (Ctrl+R)")
    print("2. Go to Query tab")
    print("3. Select 'glih-default' or create a new collection")
    print("4. Run your query again")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nThis is normal if ChromaDB hasn't been initialized yet.")
    print("Just run a query with a new collection name and it will work.")
