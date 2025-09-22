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

        # Delete old file if exists
        old_file_id = f.get("old_file_id")
        if old_file_id:
            try:
                client.files.delete(old_file_id)
                print(f"Deleted old file {old_file_id}")
            except Exception as e:
                print(f"Failed to delete old file {old_file_id}: {e}")

        # Upload new file using context manager
        try:
            with open(path, "rb") as file_handle:
                file_obj = client.files.create(
                    file=file_handle,
                    purpose="assistants"
                )
        except Exception as e:
            print(f"Failed to upload {path}: {e}")
            continue

        # Attach to vector store
        try:
            client.vector_stores.file_batches.create(
                vector_store_id=vector_store_id,
                file_ids=[file_obj.id]
            )
        except Exception as e:
            print(f"Failed to attach file {file_obj.id} to vector store: {e}")
            continue

        f["new_file_id"] = file_obj.id
        print(f"[{i}/{len(files_with_fileid)}] Uploaded {path.name}, file_id={file_obj.id}")

    return files_with_fileid
