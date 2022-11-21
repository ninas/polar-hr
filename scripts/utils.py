from google.cloud import secretmanager
from google.cloud import storage
from youtube_consts import YTConsts
import json

SAMPLES_BUCKET = "polar-workout-samples"


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


def youtube_vid_id(url):
    m = YTConsts.id_regex.match(url)
    if m is None:
        raise Exception(f"Unable to find id in url: {url}")
    return m.group(1).strip()
