"""Force reset ChromaDB - no confirmation needed."""
import shutil
from pathlib import Path

# ChromaDB path
chroma_path = Path("data/chromadb")

print("=" * 60)
print("CHROMADB FORCE RESET")
print("=" * 60)

if chroma_path.exists():
    print(f"\n📁 Found ChromaDB directory: {chroma_path}")
    try:
        size = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file()) / 1024
        print(f"   Size: {size:.2f} KB")
    except:
        pass
    
    try:
        shutil.rmtree(chroma_path)
        print("\n✅ ChromaDB directory deleted successfully")
    except Exception as e:
        print(f"\n❌ Error deleting directory: {e}")
        print("\nTry closing the backend and running this again.")
        exit(1)
else:
    print(f"\n✅ ChromaDB directory doesn't exist: {chroma_path}")
    print("   Nothing to delete.")

print("\n" + "=" * 60)
print("NEXT STEPS")
print("=" * 60)
print("\n1. ⚠️  STOP the backend (Ctrl+C in backend terminal)")
print("2. 🔄 RESTART the backend:")
print("   .\.venv\Scripts\python.exe -m uvicorn --reload --port 8000 --app-dir glih-backend/src glih_backend.api.main:app")
print("3. 🌐 REFRESH your browser (Ctrl+R or F5)")
print("4. ✅ Try your query again with 'glih-default' collection")
print("\nThe collection will be created automatically with correct dimensions (1536).")
print("=" * 60)
