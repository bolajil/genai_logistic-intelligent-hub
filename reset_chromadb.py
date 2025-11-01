"""Complete ChromaDB reset - removes all collections and data."""
import shutil
from pathlib import Path

# ChromaDB path
chroma_path = Path("data/chromadb")

print("=" * 60)
print("CHROMADB COMPLETE RESET")
print("=" * 60)

if chroma_path.exists():
    print(f"\n📁 Found ChromaDB directory: {chroma_path}")
    print(f"   Size: {sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file()) / 1024:.2f} KB")
    
    response = input("\n⚠️  This will DELETE ALL collections and data. Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        try:
            shutil.rmtree(chroma_path)
            print("\n✅ ChromaDB directory deleted successfully")
            print("\n📝 Next steps:")
            print("1. Restart the backend (Ctrl+C and restart)")
            print("2. Refresh your browser (Ctrl+R)")
            print("3. Go to Query tab")
            print("4. Select 'glih-default' collection")
            print("5. Try your query again")
            print("\nThe collection will be created automatically with correct dimensions.")
        except Exception as e:
            print(f"\n❌ Error deleting directory: {e}")
    else:
        print("\n❌ Reset cancelled")
else:
    print(f"\n✅ ChromaDB directory doesn't exist: {chroma_path}")
    print("   This is fine - it will be created automatically when you run a query.")
    print("\n📝 Next steps:")
    print("1. Make sure backend is running")
    print("2. Refresh your browser")
    print("3. Try your query with 'glih-default' collection")
