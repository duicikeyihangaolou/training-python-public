import os
from datetime import date
from storage.obs_client import build_obs_client, ObjectStorage

def main():
    store = ObjectStorage(build_obs_client(), os.environ["OBS_BUCKET"])
    key = f"lab/{date.today().isoformat()}/hello.txt"
    store.upload_bytes(key, b"hello obs", content_type="text/plain; charset=utf-8")
    assert store.download_bytes(key) == b"hello obs"
    print(store.download_bytes(key))
    print("OK", key)

if __name__ == "__main__":
    main()
