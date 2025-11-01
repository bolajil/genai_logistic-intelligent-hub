"""Quick script to delete a problematic collection."""
import requests
import sys

collection_name = sys.argv[1] if len(sys.argv) > 1 else "query_trials"

print(f"Deleting collection: {collection_name}")

try:
    r = requests.delete(f"http://localhost:8000/index/collections/{collection_name}", timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
    
    if r.status_code == 200:
        print(f"\n✅ Successfully deleted collection '{collection_name}'")
        print("\nYou can now:")
        print("1. Go to the Query tab")
        print("2. Select or create a new collection")
        print("3. Run your query again")
    else:
        print(f"\n❌ Failed to delete collection")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure the backend is running on http://localhost:8000")
