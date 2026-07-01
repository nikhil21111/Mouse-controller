# upload_release.py - Create a GitHub Release and upload the 219MB DMG asset

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error

OWNER = "nikhil21111"
REPO = "Mouse-controller"
TAG = "v1.0.0"
DMG_PATH = "dist/AirTrackpad.dmg"

def get_github_token():
    try:
        proc = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, _ = proc.communicate(input="protocol=https\nhost=github.com\n\n")
        for line in stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except Exception as e:
        print(f"[-] Failed to read credentials from git helper: {e}")
    return None

def create_release(token):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "AirTrackpad-Uploader"
    }
    
    payload = {
        "tag_name": TAG,
        "name": f"v1.0.0 - Production Release",
        "body": "macOS Air Trackpad App Installer (.dmg). Drag and drop to install. Make sure to enable Accessibility permissions in System Settings.",
        "draft": False,
        "prerelease": False
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode("utf-8"))
            print(f"[+] Release created successfully. ID: {response['id']}")
            return response["id"], response["upload_url"].split("{")[0]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        if e.code == 422 and "already_exists" in body:
            print("[*] Release already exists. Fetching release info...")
            return get_existing_release(token)
        print(f"[-] Failed to create release: {e.code} - {body}")
        sys.exit(1)

def get_existing_release(token):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "AirTrackpad-Uploader"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req) as res:
        response = json.loads(res.read().decode("utf-8"))
        return response["id"], response["upload_url"].split("{")[0]

def upload_asset(token, upload_url):
    filename = "AirTrackpad.dmg"
    url = f"{upload_url}?name={filename}"
    
    file_size = os.path.getsize(DMG_PATH)
    print(f"[+] Uploading {filename} ({file_size / (1024*1024):.2f} MB) to GitHub...")
    
    with open(DMG_PATH, "rb") as f:
        file_data = f.read()
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/octet-stream",
        "Content-Length": str(file_size),
        "User-Agent": "AirTrackpad-Uploader"
    }
    
    req = urllib.request.Request(url, data=file_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode("utf-8"))
            download_url = response.get("browser_download_url")
            print(f"[+] Asset uploaded successfully!")
            print(f"[+] Direct Download Link: {download_url}")
            return download_url
    except urllib.error.HTTPError as e:
        print(f"[-] Failed to upload asset: {e.code} - {e.read().decode('utf-8')}")
        sys.exit(1)

def main():
    if not os.path.exists(DMG_PATH):
        print(f"[-] ERROR: {DMG_PATH} not found. Run ./build_dmg.sh first.")
        sys.exit(1)
        
    token = get_github_token()
    if not token:
        print("[-] ERROR: Could not find GitHub token in git keychain helper.")
        sys.exit(1)
        
    release_id, upload_url = create_release(token)
    download_url = upload_asset(token, upload_url)
    update_readme(download_url)

def update_readme(download_url):
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            content = f.read()
            
        badge = f"\n\n## 📥 [Download AirTrackpad for macOS (DMG)]({download_url})\n\n"
        if "Download AirTrackpad for macOS" not in content:
            lines = content.split("\n")
            lines.insert(2, badge)
            new_content = "\n".join(lines)
            with open(readme_path, "w") as f:
                f.write(new_content)
            print("[+] Updated README.md with direct download link.")

if __name__ == '__main__':
    main()
