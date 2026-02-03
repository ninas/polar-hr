# polar-hr

Note to self:
* This repo uses sapling not git.
* Uses poetry (```poetry shell```)

## Scripts

Run them using ```python -m src.scripts.name_of_script```

## Connect to DB manually
```
gcp_proxy # cloud_sql_proxy --credential_file ~/.gconf/workout-serverless-deployer.json --dir=/cloudsql/
gcloud beta sql connect workout-db --database workouts
```
