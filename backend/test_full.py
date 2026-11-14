"""
Full end-to-end test: upload an image, then search with it.
"""
import requests
import io
import sys
from PIL import Image

BASE = "http://localhost:8000"

def make_test_image():
    """Create a simple test image in memory."""
    img = Image.new("RGB", (224, 224), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf

def test():
    print("\n=== Health Check ===")
    r = requests.get(f"{BASE}/api/health")
    print(f"  Status: {r.status_code}, Body: {r.json()}")
    assert r.status_code == 200, "Health check failed!"

    print("\n=== Upload Image ===")
    img_buf = make_test_image()
    r = requests.post(
        f"{BASE}/api/upload",
        files={"file": ("test_bike.jpg", img_buf, "image/jpeg")},
        data={"tags": "test,motorcycle", "description": "A test image"}
    )
    print(f"  Status: {r.status_code}")
    if r.status_code != 200:
        print(f"  ERROR: {r.text}")
        sys.exit(1)
    upload_data = r.json()
    image_id = upload_data["id"]
    print(f"  Uploaded ID: {image_id}")
    print(f"  URL: {upload_data['url']}")

    print("\n=== Text Search ===")
    r = requests.get(f"{BASE}/api/search/text?q=motorcycle&top_k=5")
    print(f"  Status: {r.status_code}")
    if r.status_code != 200:
        print(f"  ERROR: {r.text}")
        sys.exit(1)
    data = r.json()
    print(f"  Results: {data['total_results']}, Time: {data['search_time_ms']}ms")

    print("\n=== Image Search ===")
    img_buf2 = make_test_image()
    r = requests.post(
        f"{BASE}/api/search/image",
        files={"file": ("query.jpg", img_buf2, "image/jpeg")},
        data={"top_k": 5}
    )
    print(f"  Status: {r.status_code}")
    if r.status_code != 200:
        print(f"  ERROR: {r.text}")
        sys.exit(1)
    data = r.json()
    print(f"  Results: {data['total_results']}, Time: {data['search_time_ms']}ms")
    for res in data["results"]:
        print(f"    - {res['filename']}  (score={res['similarity_score']})")

    print("\n=== Collection ===")
    r = requests.get(f"{BASE}/api/collection")
    print(f"  Status: {r.status_code}")
    data = r.json()
    print(f"  Total images indexed: {data.get('total', 'N/A')}")

    print("\n✅ ALL TESTS PASSED — No 500 errors!")

if __name__ == "__main__":
    test()
