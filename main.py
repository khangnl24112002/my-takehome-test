#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv
from src.optisigns_docs.scraper import fetch_and_convert
from src.optisigns_docs.uploader import upload_files
from src.optisigns_docs.utils import file_hash, load_state, save_state

load_dotenv()

DOCS_DIR = "data/articles"
VECTOR_STORE_ID = os.environ["VECTOR_STORE_ID"]

def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    state = load_state()  # {slug: {hash, file_id}}

    added, updated, skipped = [], [], []
    files_to_upload = []

    articles = fetch_and_convert()  # list of dict {slug, title, md, url}

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

    # Upload + overwrite old files
    if files_to_upload:
        result = upload_files(VECTOR_STORE_ID, files_to_upload)
        # Update state.json với file_id mới
        for r in result:
            slug = Path(r["path"]).stem
            state[slug]["file_id"] = r["new_file_id"]
        print(f"📦 Uploaded {len(files_to_upload)} files")
    else:
        print("ℹ️ No new or updated files to upload")

    save_state(state)
    print({"added": len(added), "updated": len(updated), "skipped": len(skipped)})

if __name__ == "__main__":
    main()
