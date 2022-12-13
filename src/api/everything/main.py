from peewee import prefetch
from src.db.workout import models
from src.utils.db_utils import DBConnection
from src.utils import log
import json


def everything_http(request, is_dev=False):
    """
    /everything

    """
    logger = log.new_logger(is_dev=is_dev)
    logger.bind(path="/everything")

    db = DBConnection(logger).workout_db
    db_objects = {}
    with db.atomic():
        for mod in models.get_all_models():
            db_objects[mod.__name__] = mod.select()

        mappings = [
            ("Workouts", "Tags"),
            ("Workouts", "Sources"),
            ("Workouts", "Equipment"),
            ("Sources", "Tags"),
            ("Sources", "Workouts", "WorkoutsSourcesThrough")
        ]
        for m in mappings:
            a = m[0]
            b = m[1]
            through = m[2] if len(m) == 3 else f"{a}{b}Through"
            prefetch(db_objects[a], db_objects[through], db_objects[b])
        prefetch(db_objects["HRZones"], db_objects["Workouts"])
        prefetch(db_objects["Samples"], db_objects["Workouts"])

        logger.info(f"Total number of tags: {len(db_objects['Tags'])}")
        logger.info(f"Total number of equipment entries: {len(db_objects['Equipment'])}")
        data = {
            "tags": {tag.id: tag.json_friendly() for tag in db_objects["Tags"]},
            "equipment": {equip.id: equip.json_friendly() for equip in db_objects["Equipment"]},
            "sources": {},
            "workouts": {},
        }
        logger.info(f"Total number of sources: {len(db_objects['Sources'])}")
        for source in db_objects['Sources']:
            s = source.json_friendly()
            s["tags"] = [t.id for t in source.tags]
            s["workouts"] = [w.id for w in source.workouts]
            data["sources"][source.id] = s

        logger.info(f"Total number of workouts: {len(db_objects['Workouts'])}")
        for workout in db_objects['Workouts']:
            w = workout.json_friendly()
            w["sources"] = [s.id for s in workout.sources]
            w["equipment"] = [e.id for e in workout.equipment]
            w["tags"] = [t.id for t in workout.tags]
            w["hrzones"] = {}
            data["workouts"][workout.id] = w

        logger.info("Adding samples in")
        for sample in db_objects["Samples"]:
            data["workouts"][sample.workout.id]["samples"] = sample.samples

        logger.info("Adding hrzone info")
        for zone in db_objects['HRZones']:
            z = zone.json_friendly()
            del z["workout"]
            data["workouts"][zone.workout.id]["hrzones"][zone.zonetype] = z
    return json.dumps(data)

if __name__ == "__main__":
    print(everything_http(None, True))
