import sys
import traceback
from fastapi.testclient import TestClient
sys.path.append('e:\\Work\\Task\\image-search-engine\\backend')

from app.main import app

def run_test():
    with TestClient(app) as client:
        try:
            print("Making request...")
            response = client.get('/api/search/text?q=test')
            print("Status Code:", response.status_code)
            print("Response:", response.text)
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
