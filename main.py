#!/usr/bin/env python3
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
from pathlib import Path
from dotenv import load_dotenv
from src.optisigns_docs.scraper import fetch_and_convert

from src.optisigns_docs.uploader import upload_files
from src.optisigns_docs.utils import file_hash

load_dotenv()

DOCS_DIR = "data/articles"
VECTOR_STORE_ID = os.environ["VECTOR_STORE_ID"]
SPACES_BUCKET = os.environ["SPACES_BUCKET"]
SPACES_REGION = os.environ.get("SPACES_REGION", "nyc3")
SPACES_ENDPOINT = f"https://{SPACES_REGION}.digitaloceanspaces.com"
LAST_RUN_FILE = os.path.join(DOCS_DIR, "last_run.json")
STATE_FILE = os.path.join(DOCS_DIR, "state.json")

# Khởi tạo S3 client cho Spaces
session = boto3.session.Session()
s3_client = session.client(
    's3',
    region_name=SPACES_REGION,
    endpoint_url=SPACES_ENDPOINT,
    aws_access_key_id=os.environ["SPACES_KEY"],
    aws_secret_access_key=os.environ["SPACES_SECRET"],
    config=Config(signature_version='s3v4')
)

def upload_to_spaces(local_path, object_name, make_public=False):
    """Upload file lên Spaces, optional public read"""
    try:
        extra_args = {'ACL': 'public-read'} if make_public else {}
        s3_client.upload_file(local_path, SPACES_BUCKET, object_name, ExtraArgs=extra_args)
        url = f"https://{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/{object_name}"
        print(f"📤 Uploaded {local_path} to {url}", flush=True)
        return url
    except ClientError as e:
        print(f"❌ Spaces upload error: {e}", flush=True)
        return None

def load_state():
    """Tải state.json từ Spaces"""
    try:
        os.makedirs(DOCS_DIR, exist_ok=True)
        s3_client.download_file(SPACES_BUCKET, "state.json", STATE_FILE)
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            print("📥 Loaded state.json from Spaces", flush=True)
            return json.load(f)
    except ClientError as e:
        print(f"⚠️ No state.json found in Spaces, starting fresh: {e}", flush=True)
        return {}

def save_state(state):
    """Lưu state.json local rồi upload lên Spaces"""
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    upload_to_spaces(STATE_FILE, "state.json", make_public=False)
    print("📝 Saved state.json to Spaces", flush=True)

def save_last_run(counts):
    """Lưu counts local rồi upload lên Spaces"""
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)
    artefact_url = upload_to_spaces(LAST_RUN_FILE, "last_run.json", make_public=True)
    return artefact_url

def main():
    print("🚀 Job started", flush=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    state = load_state()

    added, updated, skipped = [], [], []
    files_to_upload = []

    print("📥 Fetching articles...", flush=True)
    articles = fetch_and_convert()
    print(f"Found {len(articles)} articles", flush=True)

    for a in articles:
        path = os.path.join(DOCS_DIR, f"{a['slug']}.md")
        new_hash = file_hash(a["md"])

        if a["slug"] not in state:
            # NEW file
            with open(path, "w", encoding="utf-8") as f:
                f.write(a["md"])
            files_to_upload.append({"path": path, "old_file_id": None})
            state[a["slug"]] = {"hash": new_hash, "file_id": None}
            added.append(path)
        elif state[a["slug"]]["hash"] != new_hash:
            # UPDATED file
            with open(path, "w", encoding="utf-8") as f:
                f.write(a["md"])
            files_to_upload.append({"path": path, "old_file_id": state[a["slug"]]["file_id"]})
            state[a["slug"]]["hash"] = new_hash
            updated.append(path)
        else:
            # SKIPPED
            skipped.append(path)

    if files_to_upload:
        print(f"📦 Uploading {len(files_to_upload)} files to vector store...", flush=True)
        result = upload_files(VECTOR_STORE_ID, files_to_upload)
        for r in result:
            slug = Path(r["path"]).stem
            state[slug]["file_id"] = r["new_file_id"]
        print(f"✅ Uploaded {len(files_to_upload)} files to vector store", flush=True)

        # Optional: Upload delta articles lên Spaces
        for path in added + updated:
            rel_path = Path(path).relative_to(DOCS_DIR)
            upload_to_spaces(path, f"articles/{rel_path}", make_public=False)
    else:
        print("ℹ️ No new or updated files to upload", flush=True)

    save_state(state)
    counts = {"added": len(added), "updated": len(updated), "skipped": len(skipped)}
    artefact_url = save_last_run(counts)
    if artefact_url:
        print(f"🔗 Last run artefact: {artefact_url}", flush=True)
    else:
        print("⚠️ Artefact upload failed", flush=True)

    print(counts, flush=True)
    print("🏁 Job completed", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        sys.exit(1)