# sourceq

## Testing
As with everything this needs to have GCP's sql auth proxy running.
```
cloud_sql_proxy --credential_file=creds.json --dir=/cloudsql/
```

Basic testing can be done using GCP's functions-framework and curl.
Run:
```
functions-framework --target sources_query_http
```

and query like:
```
curl --request POST  -H "Content-Type: application/json" -d '{"query": {"sourceAttributes": {"tags": ["hiit", "low impact"]}}}' http://localhost:8080
```
etc.
