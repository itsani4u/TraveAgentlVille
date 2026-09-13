"""
streamlit_app/gcp_utils.py
-----------------------------
Small wrapper around google-cloud-storage so the Streamlit "Ingestion"
page can upload a file to a GCS bucket. Wrapped in try/except so the whole
app doesn't crash for students who haven't set up GCP credentials yet -
the rest of the app (local FAISS index, chat) works fine without it.
"""

import config


def _get_bucket():
    """Shared connection helper used by every upload function below (and
    by logging_utils.py, which reuses this module purely for its GCS
    plumbing - it has no Streamlit dependency itself)."""
    from google.cloud import storage  # raises ImportError if not installed

    if not config.GCP_PROJECT_ID or not config.GCP_BUCKET_NAME:
        raise RuntimeError("GCP_PROJECT_ID / GCP_BUCKET_NAME are not set in .env")

    client = storage.Client(project=config.GCP_PROJECT_ID)
    return client.bucket(config.GCP_BUCKET_NAME)


def upload_file_to_bucket(local_path: str, destination_blob_name: str) -> str:
    """Uploads a local file to config.GCP_BUCKET_NAME. Returns a status
    message. Requires GOOGLE_APPLICATION_CREDENTIALS to be set in the
    environment (see README.md)."""
    try:
        bucket = _get_bucket()
    except ImportError:
        return "google-cloud-storage is not installed. Run: pip install google-cloud-storage"
    except RuntimeError as e:
        return f"{e} - skipping real upload."

    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_path)
        return f"Uploaded to gs://{config.GCP_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        return f"Upload failed: {e}"


def upload_string_to_bucket(content: str, destination_blob_name: str) -> str:
    """Uploads an in-memory string directly to the bucket (no local file
    needed). Used for quick one-off log/report snapshots."""
    try:
        bucket = _get_bucket()
    except ImportError:
        return "google-cloud-storage is not installed. Run: pip install google-cloud-storage"
    except RuntimeError as e:
        return f"{e} - skipping real upload."

    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(content)
        return f"Uploaded to gs://{config.GCP_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        return f"Upload failed: {e}"
