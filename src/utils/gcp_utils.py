from functools import cache


@cache
def fetch_from_cloud_storage(path):
    """Fetch file content from Google Cloud Storage.

    Args:
        path: GCS path in format "bucket_name/object_path"

    Returns:
        File content as UTF-8 string
    """
    from google.cloud import storage

    parts = path.split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1] if len(parts) > 1 else ""

    client = storage.Client(project="workout-368502")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_text()


@cache
def get_secret(name):

    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient(project="workout-368502")
    secret_name = f"projects/937046739753/secrets/{name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")


@cache
def fetch_config(key):
    from google.cloud import runtimeconfig

    config_client = runtimeconfig.Client()
    config = config_client.config("workout")
    var = config.get_variable(key)
    return var.text
