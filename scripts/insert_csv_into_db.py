from google.cloud import secretmanager
import psycopg2
from collections import defaultdict
import os, json, datetime, re
import googleapiclient
from googleapiclient.errors import HttpError
from utils import get_secret
from youtube import YoutubeVid

def insert_workout_row(conn, data):
    # Check if row exists
    print("Checking if row exists")
    wrk = val_in_db(
        conn,
        "workout",
        [("startTime",
          datetime.datetime.fromisoformat(data["startTime"]))]
    )
    if wrk is not None:
        print(f"{data['startTime']}: Already in DB")
        return

    vids, related = parse_note(data["note"])

    print(vids,related)
    for i in vids:
        source_id = source_row(conn, i)

    sql = "INSERT INTO workout (num) VALUES (%s)"

def source_row(conn, url):
    if not YoutubeVid.is_youtube_vid(url):
        raise Exception(f"Unknown source type: {url}")

    vid = YoutubeVid(url)

    # insert the source row itself
    insert_row_if_not_exists(
        conn,
        "sources",
        "url, sourceType, name, length, extraInfo",
        [
            url,
            "Youtube",
            vid.title,
            vid.duration,
            None
        ],
        [("url", url)]
    )
    source_data = val_in_db(conn, "sources", [("url", url)])
    source_id = source_data[0]
    print(source_id)

    # now insert tags
    print(vid.tags)
    for i in vid.tags:
        insert_row_if_not_exists(
            conn,
            "tags",
            "name, sourceID",
            [i, source_id],
            [
                ("name", i),
                ("sourceID", source_id)
            ]
        )

    # and exercises
    print(vid.exercises)
    for i in vid.exercises:
        insert_row_if_not_exists(
            conn,
            "exercises",
            "name, sourceID",
            [i, source_id],
            [
                ("name", i),
                ("sourceID", source_id)
            ]
        )

    print("\n\n")

    return source_id


def insert_row(conn, table, names, params):
    vals = ", ".join(["%s"] * len(params))
    sql = f"INSERT INTO {table} ({names}) VALUES ({vals})"
    with conn:
        with conn.cursor() as cur:
            cur.execute(cur.mogrify(sql, params))

def insert_row_if_not_exists(conn, table, names, params, conditions):
    vals = ", ".join(["%s"] * len(params))
    cond = " AND ".join([f"{k} = %s" for k, v in conditions])
    sql = (f"INSERT INTO {table}({names}) "
           f"SELECT {vals} "
           f"WHERE NOT EXISTS ( "
           f"SELECT 1 FROM {table} WHERE {cond} )")
    params.extend([v for k, v in conditions])
    with conn:
        with conn.cursor() as cur:
            cur.execute(cur.mogrify(sql, params))





def val_in_db(conn, table, params):
    condition = " AND ".join([f"{k} = %s" for k, v in params])
    sql = f"SELECT * FROM {table} WHERE {condition}"
    vals = [v for k, v in params]
    with conn:
        with conn.cursor() as cur:
            cur.execute(cur.mogrify(sql,
                                    vals))
            result = cur.fetchone()
    return result

def parse_note(data):
    attributes = {
        "equipment": [],
    }
    components = data.split(";")
    vids = components[0][15:].split(" ") \
        if components[0].startswith("Multiple") \
        else [components[0]]

    index = 1
    while index < len(components):
        title, rest = components[index].split(":")
        if title == "weights":
            for i in rest.split(","):
                dd = {"type": "Weights", "num": 2}
                i = i.trim()
                if i.startswith("one"):
                    dd["num"] = 1
                    i = i[5:]
                dd["magnitude"] = i
                attributes["equipment"].append(dd)
        elif title == "bands":
            for i in rest.split(","):
                attributes["equipment"].append({
                    "type": "Band",
                    "num": "1",
                    "magnitude": i
                })
        elif title == "note" or title == "notes":
            attributes["note"] = rest

        index += 1

    return vids, attributes

def read_files():
    all_info = []
    for f in os.listdir("/home/nina/code/polar/output"):
        if not f.startswith("training"):
            continue

        with open(f"/home/nina/code/polar/output/{f}") as fi:
            all_info.append(json.load(fi))
    return all_info

def insert_equipment(conn):
    equipment = []
    for i in ["light", "medium", "heavy", "very heavy"]:
        equipment.append(("Band", i, 1,))

    for i in ["3", "5", "8", "10", "12", "15", "20", "25"]:
        equipment.append(("Weights", i, 1,))
        equipment.append(("Weights", i, 2,))

    with conn:
        with conn.cursor() as cur:
            for val in equipment:
                cur.execute("INSERT INTO equipment (equipmentType, magnitude, quantity) VALUES (%s, %s, %s)", val)

def insert_rows(conn, data):
    for i in data:
        if "note" not in i:
            print("Note not found")
            continue
        print("FOUND")
        try:
            insert_workout_row(conn, i)
        except Exception as e:
            print(e)

def view_all_tags(data):
    seen_vids = set()
    source_tags = defaultdict(set)
    final_tags = set()
    for i in data:
        if "note" not in i:
            print("Note not found")
            continue
        print("FOUND")
        vids, related = parse_note(i["note"])
        for v in vids:
            if v in seen_vids:
                continue

            seen_vids.add(v)
            try:
                vid = YoutubeVid(v)
                print(vid.title)
                print(v)
                print(vid.tags)
                for k,v in vid.source_tags.items():
                    source_tags[k].update(v)
                final_tags.update(vid.tags)
                print("")
            except Exception as e:
                print("Errored: ",e)

    print("")
    for i in sorted(final_tags):
        print(i,source_tags[i])
    print("\n\n\n")




if __name__ == "__main__":
    conn = psycopg2.connect(
        host="34.28.182.87",
        database="workout_data",
        user="admin",
        password=get_secret("db_workout"))

    try:
        #insert_equipment(conn)

        data = read_files()

        #insert_rows(conn, data)
        view_all_tags(data)
    finally:
        conn.close()
