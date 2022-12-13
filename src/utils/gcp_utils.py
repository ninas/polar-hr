from functools import cache
import json
import asyncio

from google.cloud import secretmanager, storage, runtimeconfig
from gcloud.aio.storage import Storage


SAMPLES_BUCKET = "polar-workout-samples"


@cache
def get_secret(name):
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/937046739753/secrets/{name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")


def upload_to_cloud_storage(blob_name, data, bucket_name=SAMPLES_BUCKET):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(data))
    return f"{bucket_name}/{blob_name}"


def fetch_from_cloud_storage(blob_path):
    bucket_name, blob_name = blob_path.split("/")
    print(blob_name)
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_text()

async def async_fetch_from_cloud_storage(blob_path):
    bucket_name, blob_name = blob_path.split("/")

    async with Storage() as storage:
        bucket = storage.get_bucket(bucket_name)
        blob = await bucket.get_blob(blob_name)
        constructed_result = await blob.download()
        return constructed_result.decode('utf-8')


@cache
def fetch_config(key):
    config_client = runtimeconfig.Client()
    config = config_client.config("workout")
    var = config.get_variable(key)
    return var.text
