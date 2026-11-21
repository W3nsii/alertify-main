# ALERTIFY dataset

Open copies of the data built into ALERTIFY (Batangas City). Each dataset is given as
**CSV** (opens in Excel or Google Sheets) and **JSON**. The evacuation centers are also
given as **GeoJSON**: open [`evacuation_centers.geojson`](evacuation_centers.geojson) on
GitHub to see every center on an interactive map.

| File | Records | Contents |
|---|---|---|
| `evacuation_centers.csv` / `.json` / `.geojson` | 80 | Name, location, barangay, capacity (families / persons), longitude, latitude, note |
| `emergency_contacts.csv` / `.json` | 21 | Organization, category, phone numbers, description, primary hotline flag |
| `barangays.csv` / `.json` | 105 | The barangays of Batangas City |
| `disaster_categories.csv` / `.json` | 7 | Hazard types the app supports |
| `disaster_guide.csv` / `.json` | 149 | Disaster Guide tips: before, during, after, checklist, supplies, reminders, avoid |
| `response_instructions.csv` / `.json` | 93 | Rules the assessment engine uses to build instructions (disaster, section, condition, priority) |

## Sources and limits

* **Evacuation centers** come from *EVACUATION-CENTER-2-1.pdf* (Batangas Province evacuation
  center list), entries under *LGU: Batangas City* only. Coordinates are the X (longitude)
  and Y (latitude) values given in that source. They have **not** been verified on the ground,
  and the list does not say whether a center is open or safe for a given hazard.
* **Emergency contacts** are an initial reference list and should be confirmed before use.
* **Guidance text** is based on NDRRMC/OCD, PAGASA, PHIVOLCS, BFP and Philippine Red Cross
  public safety guidance.

Always follow official instructions from the Batangas City CDRRMO and your barangay.

## Updating

These files are generated from [`seed_data.py`](../seed_data.py). After editing it, run:

```bash
python export_data.py
```

Changes that administrators make inside the running app (for example, marking a center
verified) are stored in the app's database and are not included in these files.
