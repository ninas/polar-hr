from functools import cache


SAMPLES_BUCKET = "polar-workout-samples"


@cache
def get_secret(name):

    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
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
