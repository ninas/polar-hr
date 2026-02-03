from collections import defaultdict

import src.db.workout.models as models
from src.workout_sources.source_consts import SourceConsts
from src.utils import log
from src.utils.db_utils import DBConnection
from src.workout_sources.youtube import Youtube


def get_all_tags(logger, db):

    to_remove = set()
    to_replace = defaultdict(set)
    to_create = defaultdict(set)
    with db.atomic():
        tags = models.Tags.select().execute()

    tags_map = {i.name: i for i in tags}

    id_to_name = {i.id: i.name for i in tags}
    for tag in tags:
        if tag.name in SourceConsts.ignore_tags:
            to_remove.add(tag)
        elif tag.name in SourceConsts.dedupes:
            updated_name = SourceConsts.dedupes[tag.name]
            if updated_name in tags_map:
                to_replace[tags_map[updated_name]].add(tag)
            else:
                to_create[updated_name].add(tag)

        elif tag.tagtype == models.TagType.EXERCISE:
            updated_name = Youtube._clean_exercise(tag.name)
            if updated_name != tag.name:
                if updated_name in tags_map:
                    to_replace[tags_map[updated_name]].add(tag)
                else:
                    to_create[updated_name].add(tag)

    if len(to_remove) > 0:
        print("To remove:")
        for i in to_remove:
            print(f"\t{i.name}")
    if len(to_replace) > 0:
        print("To replace:")
        for k, v in to_replace.items():
            print(f"\t{'; '.join(vv.name for vv in v)} -> {k}")
    if len(to_create) > 0:
        print("To create")
        for k, v in to_create.items():
            print(f"\t{'; '.join(vv.name for vv in v)} -> {k}")
    return to_remove, to_replace, to_create


def update_tags(logger, db, to_remove, to_replace, to_create):
    junction = models.Sources.tags.get_through_model()

    print("CREATING NEW TAGS")
    creation_data = []
    with db.atomic():
        for new_tag_name, old_tags in to_create.items():
            tag_types = {ot.tagtype: None for ot in old_tags}
            for tt, val in tag_types.items():
                print(f"Creating new tag: {new_tag_name} ({tt})")
                tag = models.Tags(name=new_tag_name, tagtype=tt)
                tag.save()
                tag_types[tt] = tag
            for ot in old_tags:
                to_replace[tag_types[ot.tagtype]].add(ot)
                print(
                    f"\tNew replacement added: {ot.name} -> {tag_types[ot.tagtype].name}"
                )

    # updating
    update = defaultdict(set)
    mapping = {}
    for new_tag, old_tags in to_replace.items():
        # get all sources using new tag
        # get all sources using old tag
        # where there is not overlap - update the junction table, delete from tags
        # where there is overlap - delete from junction table, delete from tags
        junctions_using_new_tag = {
            i.sources_id: i
            for i in junction.select().where(junction.tags_id == new_tag.id)
        }
        sources_using_new_tag = set(k for k, v in junctions_using_new_tag.items())

        for old_tag in old_tags:
            junctions_using_old_tag = {
                i.sources_id: i
                for i in junction.select().where(junction.tags_id == old_tag.id)
            }
            sources_using_old_tag = set(k for k, v in junctions_using_old_tag.items())

            for k, v in junctions_using_old_tag.items():
                mapping[v] = old_tag
            needs_update = sources_using_old_tag - sources_using_new_tag
            for i in needs_update:
                update[new_tag].add(junctions_using_old_tag[i])

        to_remove |= old_tags

    print("UPDATING TAGS")
    with db.atomic():
        for new_tag, junc in update.items():
            print(f"\n\nUpdating to: {new_tag.name} ({new_tag.id})")
            for row in junc:
                print(f"\tOld tag: {mapping[row].name} ({mapping[row].id})")
                print("\t", row.id, row.tags_id, row.sources_id)
                row.tags_id = new_tag.id
                row.save()
                print("\t", row.id, row.tags_id, row.sources_id)

    # deleting from junction and then tags
    print("DELETING TAGS")
    for i in to_remove:
        name = i.name
        print(f"Deleting {name}")
        with db.atomic():
            tr = junction.delete().where(junction.tags_id == i.id).execute()
            print(f"  From junction table: {tr}")
            r = i.delete_instance()
            print(f"  From tags table: {r}")


if __name__ == "__main__":

    logger = log.new_logger(is_dev=True)

    db = DBConnection(logger).workout_db
    to_remove, to_replace, to_create = get_all_tags(logger, db)

    if len(to_remove) == 0 and len(to_replace) == 0 and len(to_create) == 0:
        print("No tags need updating")
        exit()

    print("continue?")
    ans = input()
    if ans != "y":
        exit()

    update_tags(logger, db, to_remove, to_replace, to_create)
