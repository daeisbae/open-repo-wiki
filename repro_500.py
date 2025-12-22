import requests
import json
import sys

# Force ipv4 to avoid potential ipv6 issues if any
import socket
socket.setdefaulttimeout(30)

url = "https://z7ts3d2be3.execute-api.us-east-1.amazonaws.com/v1/repos/daeisbae/open-repo-wiki/tree"
params = {
    "branch": "main",
    "path": "frontend"
}

# Mimic Browser Headers EXACTLY
headers = {
    "host": "z7ts3d2be3.execute-api.us-east-1.amazonaws.com",
    "connection": "keep-alive",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
    "accept": "application/json",
    "sec-ch-ua-mobile": "?0",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "sec-ch-ua-platform": '"macOS"',
    "origin": "https://openrepowiki.xyz",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://openrepowiki.xyz/",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
}

print(f"Testing URL: {url}")
print(f"Params: {params}")

try:
    print("\n--- Sending request ---")
    response = requests.get(url, params=params, headers=headers)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print("Response Body First 200 chars:")
    print(response.text[:200])
    
except Exception as e:
    print(f"\nEXCEPTION: {e}")
