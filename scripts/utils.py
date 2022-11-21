from google.cloud import secretmanager
from youtube_consts import YTConsts


def get_secret(name):
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/937046739753/secrets/{name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")


def youtube_vid_id(url):
    m = YTConsts.id_regex.match(url)
    if m is None:
        raise Exception(f"Unable to find id in url: {url}")
    return m.group(1).strip()
