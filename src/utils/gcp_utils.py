from functools import cache
import json

from google.cloud import secretmanager, storage, runtimeconfig


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


@cache
def fetch_config(key):
    config_client = runtimeconfig.Client()
    config = config_client.config("workout")
    var = config.get_variable(key)
    return var.text