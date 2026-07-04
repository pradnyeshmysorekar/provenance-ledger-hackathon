"""
Standalone credential check — bypasses Genblaze entirely so we can see
whether the NVIDIA key itself is valid, independent of the rest of the
pipeline. Run this directly:

    python check_nvidia_key.py
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("NVIDIA_API_KEY")

if not key:
    print("NVIDIA_API_KEY is not set in your environment / .env file.")
    raise SystemExit(1)

print(f"Using key starting with: {key[:12]}...")

r = httpx.get(
    "https://integrate.api.nvidia.com/v1/models",
    headers={"Authorization": f"Bearer {key}"},
)

print(f"HTTP status: {r.status_code}")
if r.status_code == 200:
    print("Key is VALID. Sample of models this key can access:")
    for m in r.json().get("data", [])[:5]:
        print(f"  - {m.get('id')}")
else:
    print("Key rejected. Full response body below:")
    print(r.text)
