# sourceq

## Testing

## Local
As with everything this needs to have GCP's sql auth proxy running.
```
cloud_sql_proxy --credential_file=creds.json --dir=/cloudsql/
```

Basic testing can be done using GCP's functions-framework and curl because serverless' GCP support is trash.
Run:
```
functions-framework --target sources_http
```

and query like:
```
curl --request GET http://localhost:8080
curl --request POST  -H "Content-Type: application/json" -d '{"query": {"sourceAttributes": {"tags": ["hiit", "low impact"]}}}' http://localhost:8080

```
etc.

## Remote
Serverless doesn't provide a way to invoke the remote function with a GET request, so we need to use curl

```
ACCOUNT=<account with permission to invoke>
FUNC=api-dev-sources
curl --request GET -H "Authorization: bearer $(gcloud --account $ACCOUNT auth print-identity-token)"  $(gcloud --account $ACCOUNT functions describe $FUNC | grep "url:" | awk '{ print $2 }')
```
