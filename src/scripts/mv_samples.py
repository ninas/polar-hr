import json
import asyncio

from src.utils import gcp_utils, log, db_utils
from src.db.workout import models


async def get_sample_set(w):
    print(w.samples)
    data = await gcp_utils.async_fetch_from_cloud_storage(w.samples)
    return w, json.loads(data)


async def gather_samples(workouts):
    return await asyncio.gather(*[get_sample_set(w) for w in workouts])


def samples_to_jsonb(db):
    with db.atomic():
        objs = models.Workouts.select()
    data = asyncio.run(gather_samples(objs))

    with db.atomic():
        to_insert = [
            {"samples": samples, "workout": w}
            for w, samples in sorted(data, key=lambda x: x[0].id)
        ]
        print("inserting")
        models.Samples.insert_many(to_insert).on_conflict_ignore().execute()


def main():
    logger = log.new_logger(is_dev=True)
    db = db_utils.DBConnection(logger).workout_db
    samples_to_jsonb(db)


if __name__ == "__main__":
    main()
