import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def upload_files(vector_store_id, files_with_fileid):
    """
    Upload files to vector store, overwrite old versions if file_id exists.
    files_with_fileid = list of dicts: {"path": str, "old_file_id": str|None}
    """
    for i, f in enumerate(files_with_fileid, start=1):
        path = Path(f["path"])

        # Xóa file cũ nếu có
        if f.get("old_file_id"):
            try:
                client.files.delete(f["old_file_id"])
                print(f"Deleted old file {f['old_file_id']}")
            except Exception as e:
                print(f"Failed to delete old file {f['old_file_id']}: {e}")

        # Upload file mới
        file_obj = client.files.create(
            file=open(path, "rb"),
            purpose="assistants"
        )

        # Attach vào vector store
        client.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=[file_obj.id]
        )

        f["new_file_id"] = file_obj.id
        print(f"[{i}/{len(files_with_fileid)}] Uploaded {path.name}, file_id={file_obj.id}")

    return files_with_fileid
