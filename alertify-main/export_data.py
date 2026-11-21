"""Export ALERTIFY's built-in dataset to open files in the data/ folder.

Run:   python export_data.py

Writes CSV (opens in Excel / Google Sheets), JSON, and GeoJSON (GitHub shows
it as an interactive map) for every dataset in seed_data.py, so the data can be
read without running the app.  Re-run it after editing seed_data.py.
"""
import csv
import json
import os

import seed_data

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ------------------------------------------------------------------ writers
def write_csv(name, header, rows):
    """Write rows (lists/tuples) under a header row to data/<name>.csv."""
    path = os.path.join(DATA_DIR, name + ".csv")
    # utf-8-sig adds a BOM so Excel shows characters like "ñ" and "–" correctly.
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def write_json(name, data):
    """Write data to data/<name> as pretty-printed UTF-8 JSON."""
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def records(header, rows):
    """Turn rows into a list of dicts keyed by the header names."""
    return [dict(zip(header, row)) for row in rows]


# ------------------------------------------------------------------ datasets
def export_evacuation_centers():
    header = ["name", "location", "barangay", "capacity_families", "capacity_persons",
              "longitude", "latitude", "note"]
    rows = [list(c) for c in seed_data.EVACUATION_CENTERS]
    write_csv("evacuation_centers", header, rows)
    write_json("evacuation_centers.json", records(header, rows))

    # GeoJSON uses [longitude, latitude] order; the source X/Y columns already match it.
    features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": {"name": name, "location": loc, "barangay": brgy,
                       "capacity_families": fam, "capacity_persons": persons,
                       "note": note, "source": seed_data.SOURCE_PDF},
    } for name, loc, brgy, fam, persons, lng, lat, note in seed_data.EVACUATION_CENTERS
        if lat is not None and lng is not None]
    write_json("evacuation_centers.geojson", {"type": "FeatureCollection", "features": features})
    return len(rows)


def export_contacts():
    header = ["organization", "category", "numbers", "description", "is_primary"]
    rows = [list(c) for c in seed_data.CONTACTS]
    write_csv("emergency_contacts", header, rows)
    write_json("emergency_contacts.json", records(header, rows))
    return len(rows)


def export_barangays():
    rows = [[b] for b in seed_data.BARANGAYS]
    write_csv("barangays", ["barangay"], rows)
    write_json("barangays.json", seed_data.BARANGAYS)
    return len(rows)


def export_categories():
    header = ["code", "name", "icon", "description"]
    rows = [list(c) for c in seed_data.CATEGORIES]
    write_csv("disaster_categories", header, rows)
    write_json("disaster_categories.json", records(header, rows))
    return len(rows)


def export_guide():
    """Disaster Guide: one row per tip (disaster, section, order, text)."""
    header = ["disaster", "section", "order", "text"]
    rows = [[disaster, section, i, text]
            for disaster, sections in seed_data.GUIDE.items()
            for section, lines in sections.items()
            for i, text in enumerate(lines, start=1)]
    write_csv("disaster_guide", header, rows)
    write_json("disaster_guide.json", seed_data.GUIDE)
    return len(rows)


def export_response_instructions():
    header = ["disaster", "section", "condition", "text", "priority"]
    rows = [list(r) for r in seed_data.RESPONSE_INSTRUCTIONS]
    write_csv("response_instructions", header, rows)
    write_json("response_instructions.json", records(header, rows))
    return len(rows)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    counts = {
        "evacuation centers": export_evacuation_centers(),
        "emergency contacts": export_contacts(),
        "barangays": export_barangays(),
        "disaster categories": export_categories(),
        "guide tips": export_guide(),
        "response instructions": export_response_instructions(),
    }
    for label, n in counts.items():
        print(f"{n:>4}  {label}")
    print(f"Saved to {DATA_DIR}")


if __name__ == "__main__":
    main()
