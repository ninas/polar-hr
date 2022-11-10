import os,json, pprint
from datetime import datetime, timezone, timedelta
from collections import defaultdict

pp = pprint.PrettyPrinter(indent=4)
DEBUG = False

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

def get_datetime(data, field, tz=None):
    if tz is None:
        tz = data["timeZoneOffset"] if "timeZoneOffset" in data else -420
    return datetime.fromisoformat(f"{data[field]}{tz/60:+03.0f}:00").astimezone(timezone.utc)

def read_polar_data(f):
    with open(f"/home/nina/code/polar/polar/{f}") as fi:
        contents = json.load(fi)
        contents["filename"] = f
    return get_datetime(contents, "startTime"), contents


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
        if blob["subtitles"][0]["name"] != "Heather Robertson":
            continue

        dt = datetime.fromisoformat(f"{blob['time'][:-1]}+00:00")
        blob["time"] = dt
        search_data[dt.date()].append(blob)

    for k, v in search_data.items():
        v.sort(key=lambda x: x["time"])

    return search_data

def merge_data(polar, youtube):
    for dt, v in polar.items():

        if DEBUG:
            for i in v["exercises"]:
                i["samples"]= "..."
        if "note" in v:
            print(f"Merge: Note already exists - {v['note']}\n")

            continue
        if dt.date() not in youtube:
            print(f"Merge: No potential youtube video found for time {dt}")
            continue

        latest_before_end = None
        watched_vids = []
        end = get_datetime(v, "stopTime")
        start = get_datetime(v, "startTime")
        after_start = []

        for vid in youtube[dt.date()]:
            if vid["time"] > end or end - vid["time"] < timedelta(minutes=5):
                continue
            elif vid["time"] > start:
                after_start.append(vid)

            if latest_before_end is None:
                latest_before_end = vid
                continue


            if vid["time"] - latest_before_end["time"] > timedelta(minutes=5) and vid["time"] - start > timedelta(minutes=10):
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

        polar[dt]["note"] = '; '.join([i['titleUrl'] for i in watched_vids])
        if len(watched_vids) > 1:
            polar[dt]["note"] = f"Multiple videos: {polar[dt]['note']}"
        name = v["name"] if "name" in v else ', '.join([i["sport"] for i in v["exercises"]])
        print(f"Updated {dt}: exercise type - {name}: {polar[dt]['note']}")
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

def convert_to_utc(data):
    data["startTime"] = str(get_datetime(data, "startTime"))
    if "stopTime" in data:
        data["stopTime"] = str(get_datetime(data, "stopTime"))
    for i in data["exercises"]:
        if "startTime" in i:
            i["startTime"] = str(get_datetime(i, "startTime", data["timeZoneOffset"]))
        if "stopTime" in i:
            i["stopTime"] = str(get_datetime(i, "stopTime", data["timeZoneOffset"]))
        if "samples" in i and "heartRate" in i["samples"]:
            for j in i["samples"]["heartRate"]:
                j["dateTime"] = str(get_datetime(j, "dateTime", data["timeZoneOffset"]))


def write_out(polar, location):
    if not os.path.exists(location):
        os.makedirs(location)

    for k,v in polar.items():

        if DEBUG:
            pp.pprint(v)
        convert_to_utc(v)
        with open(os.path.join(location, v["filename"]), 'w') as f:
             f.write(json.dumps(v))

if __name__ == "__main__":
    polar = read_polar_dir()
    youtube = preprocess_yt(read_youtube_data())
    merge_data(polar, youtube)
    write_out(polar, "output")
