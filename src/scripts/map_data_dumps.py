import os, json, pprint
from datetime import datetime, timedelta
from collections import defaultdict
from src.scripts.dump_workout_data_store import DumpWorkoutDataStore
from functools import cache

pp = pprint.PrettyPrinter(indent=4)
DEBUG = False

ignore_matches = {
    "training-session-2021-02-13",
    "training-session-2021-02-17",
    "training-session-2021-02-18",
    "training-session-2021-02-23",
    "training-session-2021-03-15",
    "training-session-2021-04-01",
    "training-session-2021-06-16",
    "training-session-2021-08-24",
    "training-session-2021-09-06",
    "training-session-2021-09-10",
    "training-session-2021-11-11",
    "training-session-2022-07-21",
}


def read_polar_dir():
    dd = lambda x: defaultdict(list)

    data = defaultdict(dd)
    all_info = {}
    for f in os.listdir("/home/nina/code/polar/polar"):
        if not f.startswith("training"):
            continue
        start, d = read_polar_data(f)
        all_info[start] = d
    return all_info


def read_polar_data(f):
    with open(f"/home/nina/code/polar/polar/{f}") as fi:
        contents = json.load(fi)
        if f in read_mappings():
            print("Applying mapping:")
            print(f"\t{contents['note']}")
            contents["note"] = read_mappings()[f]
            print(f" --> {contents['note']}")

        dump_wd = DumpWorkoutDataStore(contents, f)
    return dump_wd.start_time, dump_wd


def read_youtube_data():
    with open("/home/nina/code/polar/history/watch-history.json") as f:
        contents = json.load(f)
    return contents


def preprocess_yt(data):
    search_data = defaultdict(list)
    for blob in data:
        if "subtitles" not in blob:
            continue
        if len(blob["subtitles"]) != 1:
            continue

        dt = datetime.fromisoformat(f"{blob['time'][:-1]}+00:00")
        blob["time"] = dt
        search_data[dt.date()].append(blob)

    for k, v in search_data.items():
        v.sort(key=lambda x: x["time"])

    return search_data


def merge_data(polar, youtube):
    for dt in sorted(polar.keys(), key=lambda x: polar[x].filename):

        v = polar[dt]
        print(v.filename)

        if v.has_original_note:
            print(f"Merge: Note already exists\n")
            continue
        if v.filename[:27] in ignore_matches:
            print("Known mismatch, skipping")
            continue
        if dt.date() not in youtube:
            print(f"Merge: No potential youtube video found for time {dt}")
            continue

        latest_before_end = None
        watched_vids = []
        end = v.end_time
        start = v.start_time
        after_start = []

        for vid in youtube[dt.date()]:
            if vid["time"] > end or end - vid["time"] < timedelta(minutes=5):
                continue
            elif vid["time"] > start:
                after_start.append(vid)

            if latest_before_end is None:
                latest_before_end = vid
                continue

            if vid["time"] - latest_before_end["time"] > timedelta(minutes=5) and vid[
                "time"
            ] - start > timedelta(minutes=10):
                watched_vids.append(latest_before_end)
                if DEBUG:
                    print("possibly watched two videos!")
                    print("vid1:")
                    pp.pprint(latest_before_end)
                    print("vid2")
                    pp.pprint(vid)
                    print("")

            if vid["time"] > latest_before_end["time"]:
                latest_before_end = vid

        if latest_before_end is None:
            print(f"Merge: No timeperiod matching video found: {dt}")
            if DEBUG:
                pp.pprint(v)
                pp.pprint(youtube[dt.date()])
            continue

        watched_vids.append(latest_before_end)
        for i in watched_vids:
            print("CHANNEL: ",i["subtitles"][0]["name"])
        polar[dt]._sources = [i["titleUrl"] for i in watched_vids]
        print(f"Updated {dt}: exercise type - {v.sport}: {polar[dt].sources}")
        if DEBUG:
            for i in watched_vids:
                print(f"\t{i['title']} - \t\t{i['time']}")
        print("")
        print(f"Polar start: {dt}")
        print(f"Video start: {watched_vids[0]['time']}")
        print(f"Polar end: {end}")
        if DEBUG:
            print("")
            print("All vids for the day")
            pp.pprint(youtube[dt.date()])

        if DEBUG and len(after_start) > 0:
            print("Videos viewed after polar start time:")
            pp.pprint(after_start)

        print("\n\n\n")


def write_out(polar, location):
    if not os.path.exists(location):
        os.makedirs(location)

    for k, v in polar.items():
        if DEBUG:
            print(v.note, v.filename)
            pp.pprint(v)
        with open(os.path.join(location, v.filename), "w") as f:
            f.write(json.dumps(v.as_dict(), indent=4, sort_keys=True))


def append_mapping(filename, note):
    with open("mapping", "a") as f:
        f.write(f"{filename} {note}\n")


@cache
def read_mappings():
    mapping = {}
    with open("mapping") as f:
        for i in f:
            vals = i.split(" ")
            if len(vals) > 2:
                val = " ".join(vals[1:])
            mapping[vals[0]] = val
    return mapping


"""
def confirm_notes(data):
    mapping = read_mappings()
    print(mapping)

    sort_func = lambda x: polar[x].filename
    for k in sorted(data.keys(), key=sort_func):
        v = data[k]
        if "note" not in v:
            continue
        print(v.filename)
        inp = (
            mapping[v.filename]
            if v.filename in mapping
            else input(f"{v.sources} ; {v.equipment} ; {v.note} ")
        )
        if len(inp) > 0:
            inp = inp.split("\n")[0]
            v["note"] = inp
            if v["filename"] not in mapping:
                append_mapping(v["filename"], v["note"])
        """

if __name__ == "__main__":
    polar = read_polar_dir()
    youtube = preprocess_yt(read_youtube_data())
    merge_data(polar, youtube)
    # confirm_notes(polar)
    write_out(polar, "output")
