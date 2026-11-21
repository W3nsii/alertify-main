"""ALERTIFY assessment engine.

Turns a user's answers into (a) condition flags, (b) a severity level, and
(c) a set of instructions pulled from the DisasterInstruction table — so any
instruction an administrator edits is immediately reflected in new reports.
The result is an automated aid, NOT an official order.
"""
import math

from models import DisasterInstruction, EvacuationCenter

YES_NO = [{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}]
YES_NO_UNSURE = YES_NO + [{"value": "unsure", "label": "Not sure"}]


def q(key, label, options, required=True):
    return {"key": key, "label": label, "options": options, "required": required}


QUESTIONS = {
    "flood": [
        q("water_level", "What is the current water level?", [
            {"value": "none", "label": "No flooding"}, {"value": "ankle", "label": "Ankle-deep"},
            {"value": "knee", "label": "Knee-deep"}, {"value": "waist", "label": "Waist-deep"},
            {"value": "chest", "label": "Chest-deep"}, {"value": "above_head", "label": "Above head level"}]),
        q("inside_house", "Are you currently inside your house?", YES_NO),
        q("water_rising", "Is the water rising?", YES_NO_UNSURE),
        q("trapped", "Are you trapped?", YES_NO),
        q("injured", "Is anyone injured?", YES_NO),
    ],
    "typhoon": [
        q("strong_winds", "Is your area experiencing strong winds?", YES_NO),
        q("house_damage", "Is your house damaged?", [
            {"value": "none", "label": "No damage"}, {"value": "minor", "label": "Minor damage"},
            {"value": "major", "label": "Major damage (roof/walls)"}]),
        q("lines_down", "Are there fallen trees or electrical wires near you?", YES_NO),
        q("flooding", "Is your location experiencing flooding?", YES_NO),
        q("trapped", "Are you trapped?", YES_NO),
        q("injured", "Is anyone injured?", YES_NO),
    ],
    "earthquake": [
        q("shaking", "Are you currently experiencing shaking?", YES_NO),
        q("position", "Where are you right now?", [
            {"value": "inside", "label": "Inside a building"}, {"value": "outside", "label": "Outside / open area"},
            {"value": "vehicle", "label": "In a vehicle"}]),
        q("building_damaged", "Is the building damaged?", YES_NO_UNSURE),
        q("structural_damage", "Is there visible structural damage (cracks, collapsed parts)?", YES_NO),
        q("trapped", "Are you trapped?", YES_NO),
        q("injured", "Are you or anyone with you injured?", YES_NO),
    ],
    "fire": [
        q("fire_proximity", "How near is the fire to your location?", [
            {"value": "same_building", "label": "In my building"}, {"value": "nearby", "label": "Nearby / next door"},
            {"value": "far", "label": "In the area but not close"}]),
        q("building_affected", "Is your building affected?", YES_NO),
        q("smoke", "Is there smoke where you are?", YES_NO),
        q("trapped", "Are you trapped?", YES_NO),
        q("injured", "Are there injured individuals?", YES_NO),
    ],
    "volcanic": [
        q("ashfall", "Is there ashfall in your area?", [
            {"value": "none", "label": "None"}, {"value": "light", "label": "Light"}, {"value": "heavy", "label": "Heavy"}]),
        q("evac_order", "Has an evacuation order been issued for your area?", YES_NO_UNSURE),
        q("breathing", "Is anyone having difficulty breathing?", YES_NO),
        q("indoors", "Are you indoors?", YES_NO),
        q("injured", "Is anyone injured?", YES_NO),
    ],
    "landslide": [
        q("occurred", "Has a landslide already happened near you?", YES_NO),
        q("signs", "Have you noticed warning signs (ground cracks, tilting trees, rumbling, muddy creek water)?", YES_NO),
        q("near_slope", "Is your location on or below a slope?", YES_NO),
        q("heavy_rain", "Is there continuous heavy rain?", YES_NO),
        q("trapped", "Are you or someone trapped?", YES_NO),
        q("injured", "Is anyone injured?", YES_NO),
    ],
    "other": [
        q("immediate_danger", "Are you in immediate danger right now?", YES_NO),
        q("trapped", "Are you trapped?", YES_NO),
        q("injured", "Is anyone injured?", YES_NO),
    ],
}

SPECIAL_ASSISTANCE = [
    ("children", "Children"), ("elderly", "Elderly"), ("pregnant", "Pregnant individuals"),
    ("pwd", "Persons with disabilities"), ("medical", "Medical condition / needs medicine"),
    ("pets", "Pets / animals"),
]
VULNERABLE_KEYS = {"children", "elderly", "pregnant", "pwd", "medical"}

SECTIONS = [
    ("immediate", "Immediate actions"),
    ("avoid", "Things to avoid"),
    ("bring", "Essential items to bring"),
    ("evacuate", "When to evacuate"),
    ("contact", "When to contact emergency services"),
]

SEVERITY_LABELS = {
    "low": "Low", "moderate": "Moderate", "high": "High", "critical": "Critical",
}


def validate_answers(code, answers):
    """Return list of error strings; also strips unknown keys/values."""
    errors, clean = [], {}
    for question in QUESTIONS.get(code, []):
        allowed = {o["value"] for o in question["options"]}
        val = answers.get(question["key"])
        if val in allowed:
            clean[question["key"]] = val
        elif question["required"]:
            errors.append(f'Please answer: "{question["label"]}"')
    return errors, clean


def compute_flags(code, a, special):
    f = set()
    yes = lambda k: a.get(k) == "yes"
    if yes("trapped"):
        f.add("trapped")
    if yes("injured"):
        f.add("injured")
    if VULNERABLE_KEYS & set(special):
        f.add("vulnerable")

    if code == "flood":
        lvl = a.get("water_level")
        if lvl in ("ankle", "knee"):
            f.add("flood.shallow")
        if lvl in ("waist", "chest", "above_head"):
            f.add("flood.deep")
        if lvl in ("chest", "above_head"):
            f.add("flood.life_threatening")
        if yes("water_rising"):
            f.add("flood.rising")
        if yes("inside_house"):
            f.add("flood.indoors")
    elif code == "typhoon":
        if yes("strong_winds"):
            f.add("typhoon.winds")
        if a.get("house_damage") == "major":
            f.add("typhoon.house_major")
        elif a.get("house_damage") == "minor":
            f.add("typhoon.house_minor")
        if yes("lines_down"):
            f.add("typhoon.lines_down")
        if yes("flooding"):
            f.add("typhoon.flooding")
    elif code == "earthquake":
        pos = a.get("position")
        if yes("shaking"):
            f.add({"inside": "quake.shaking_inside", "outside": "quake.shaking_outside"}.get(pos, "quake.shaking_inside"))
        if pos == "vehicle":
            f.add("quake.vehicle")
        if yes("building_damaged") or yes("structural_damage"):
            f.add("quake.damaged")
    elif code == "fire":
        prox = a.get("fire_proximity")
        if prox == "same_building" or yes("building_affected"):
            f.add("fire.in_building")
        elif prox == "nearby":
            f.add("fire.nearby")
        if yes("smoke"):
            f.add("fire.smoke")
    elif code == "volcanic":
        if a.get("ashfall") in ("light", "heavy"):
            f.add("volcano.ashfall")
        if a.get("ashfall") == "heavy":
            f.add("volcano.heavy_ash")
        if yes("evac_order"):
            f.add("volcano.evac_order")
        if yes("breathing"):
            f.add("volcano.breathing")
    elif code == "landslide":
        if yes("signs"):
            f.add("landslide.signs")
        if yes("occurred"):
            f.add("landslide.occurred")
        if yes("near_slope"):
            f.add("landslide.slope")
        if yes("heavy_rain"):
            f.add("landslide.rain")
    elif code == "other":
        if yes("immediate_danger"):
            f.add("other.danger")
    return f


WEIGHTS = {
    "trapped": 60, "injured": 30, "vulnerable": 10,
    "flood.shallow": 15, "flood.deep": 45, "flood.life_threatening": 30, "flood.rising": 20, "flood.indoors": 0,
    "typhoon.winds": 15, "typhoon.house_minor": 15, "typhoon.house_major": 40,
    "typhoon.lines_down": 20, "typhoon.flooding": 20,
    "quake.shaking_inside": 25, "quake.shaking_outside": 15, "quake.vehicle": 15, "quake.damaged": 35,
    "fire.in_building": 60, "fire.nearby": 30, "fire.smoke": 20,
    "volcano.ashfall": 15, "volcano.heavy_ash": 20, "volcano.evac_order": 40, "volcano.breathing": 45,
    "landslide.signs": 40, "landslide.occurred": 35, "landslide.slope": 15, "landslide.rain": 15,
    "other.danger": 50,
}
FORCE_CRITICAL = {"trapped", "flood.life_threatening", "fire.in_building", "volcano.breathing"}


def assess_severity(flags, people_count):
    score = 10 + sum(WEIGHTS.get(f, 0) for f in flags)
    if people_count and people_count >= 10:
        score += 10
    score = min(score, 100)
    if flags & FORCE_CRITICAL:
        level = "critical"
        score = max(score, 85)
    elif score >= 70:
        level = "critical"
    elif score >= 45:
        level = "high"
    elif score >= 25:
        level = "moderate"
    else:
        level = "low"
    if "injured" in flags and level in ("low", "moderate"):
        level, score = "high", max(score, 45)
    return level, score


def immediate_danger(flags):
    return bool(flags & (FORCE_CRITICAL | {"injured", "other.danger", "landslide.occurred", "flood.deep"}))


def build_instructions(code, flags):
    active = flags | {"base"}
    rows = (DisasterInstruction.query
            .filter(DisasterInstruction.context == "response",
                    DisasterInstruction.active.is_(True),
                    DisasterInstruction.disaster.in_([code, "general"]))
            .order_by(DisasterInstruction.priority, DisasterInstruction.id).all())
    out = {s: [] for s, _ in SECTIONS}
    seen = set()
    for r in rows:
        if r.condition in active and r.section in out and r.text not in seen:
            seen.add(r.text)
            out[r.section].append({"text": r.text, "urgent": r.condition != "base"})
    # Disaster-specific lines first, then general ones, while keeping urgent lines on top.
    for s in out:
        out[s].sort(key=lambda x: (not x["urgent"],))
    return out


def haversine_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def nearest_centers(lat, lng, hazard=None, limit=5):
    """Nearest active centers with coordinates.

    If the administrator has verified hazard suitability for some centers, centers
    tagged for this hazard are returned first; untagged ones are still listed but
    flagged as 'suitability not verified'.
    """
    centers = EvacuationCenter.query.filter(EvacuationCenter.active.is_(True),
                                            EvacuationCenter.latitude.isnot(None)).all()
    ranked = []
    for c in centers:
        d = haversine_km(lat, lng, c.latitude, c.longitude)
        suitable = bool(hazard) and hazard in c.hazard_list
        # Prefer verified-suitable centers, but only if they are reasonably close.
        ranked.append((0 if suitable and d <= 10 else 1, d, c, suitable))
    ranked.sort(key=lambda t: (t[0], t[1]))
    return [(c, d, suitable) for _, d, c, suitable in ranked[:limit]]


# ---------------------------------------------------------------- safety planner
# "Where should I go and what should I do?" for a location the user typed,
# pinned on the map, or shared by GPS.  Kept separate from the report flow so
# it can be used before a disaster (planning) as well as during one.

WALK_SPEED_KMH = 4.0     # conservative adult walking pace, used for time estimates
FAR_CENTER_KM = 3.0      # beyond this, warn that reaching the center takes time
OUT_OF_RANGE_KM = 20.0   # beyond this, the user is likely outside the city's coverage
PLAN_STAGES = ("prepare", "now")

# Hazards where you should NOT head out to an evacuation center while the event
# is still happening; the first priority is protecting yourself where you are.
SHELTER_FIRST = {
    "earthquake": "Do not run outside while the ground is shaking. Drop, Cover, and Hold On. "
                  "Move to an open area away from buildings, posts and wires only after the shaking stops.",
    "typhoon": "If the typhoon has already made landfall and winds are strong, stay inside a sturdy building "
               "away from windows. Travel only when winds ease or when rescuers tell you to move.",
}


def walking_minutes(km):
    """Rough walking time in whole minutes for a straight-line distance."""
    if km is None:
        return None
    return max(1, round(km / WALK_SPEED_KMH * 60))


def distance_advice(nearest_km, hazard, stage):
    """Advice that depends on how far the nearest evacuation center is."""
    if nearest_km is None:
        return ["No evacuation center with map coordinates was found. Call the Batangas City CDRRMO "
                "or your barangay hall to ask where to evacuate."]
    if nearest_km > OUT_OF_RANGE_KM:
        return [f"The nearest Batangas City evacuation center is {nearest_km:.0f} km away, too far to reach on foot. "
                "Contact your local DRRMO or barangay for the evacuation center that serves your area."]
    mins = walking_minutes(nearest_km)
    where = f"The nearest center is about {nearest_km:.1f} km away (around {mins} min on foot, straight-line)."
    if stage == "now" and hazard in SHELTER_FIRST:
        return [SHELTER_FIRST[hazard], where]
    if nearest_km > FAR_CENTER_KM:
        tip = ("Leave early and arrange a ride with family, neighbors or your barangay. "
               "If roads become unsafe, go to the nearest sturdy, elevated building and call for help.")
    else:
        tip = "It is within walking distance. Walk with your household and keep everyone together."
    return [where, tip]


def guide_lines(hazard, sections, limit):
    """First `limit` Disaster Guide lines for a hazard from the given sections, in order."""
    rows = (DisasterInstruction.query
            .filter(DisasterInstruction.context == "guide",
                    DisasterInstruction.active.is_(True),
                    DisasterInstruction.disaster == hazard,
                    DisasterInstruction.section.in_(sections))
            .order_by(DisasterInstruction.priority, DisasterInstruction.id).all())
    by_section = {s: [r.text for r in rows if r.section == s] for s in sections}
    lines = [t for s in sections for t in by_section[s]]
    return lines[:limit]


def safety_plan(lat, lng, hazard, stage, limit=3):
    """Nearest centers plus a step-by-step list of what to do.

    `hazard` is a disaster category code (or '' for general advice) and
    `stage` is 'prepare' (no emergency yet) or 'now' (it is happening).
    Returns a plain dict ready to be sent as JSON.
    """
    nearby = nearest_centers(lat, lng, hazard=hazard or None, limit=limit)
    centers = []
    for center, km, suitable in nearby:
        item = center.to_dict()
        item.update(distance_km=round(km, 2), walk_min=walking_minutes(km), suitable=suitable)
        centers.append(item)

    nearest_km = nearby[0][1] if nearby else None
    steps = distance_advice(nearest_km, hazard, stage)
    if hazard:
        if stage == "now":
            steps += guide_lines(hazard, ["during"], 5)
            avoid = guide_lines(hazard, ["avoid"], 4)
        else:
            steps += guide_lines(hazard, ["before", "checklist"], 6)
            avoid = guide_lines(hazard, ["reminders"], 3)
    else:
        avoid = []
    steps.append("Follow evacuation orders from the Batangas City government, CDRRMO and your barangay. "
                 "This plan is a guide only and does not replace official instructions.")
    if stage == "now":
        steps.insert(0, "If anyone is trapped, injured, or in immediate danger, call 911 now.")

    return {"centers": centers, "steps": steps, "avoid": avoid,
            "nearest_km": round(nearest_km, 2) if nearest_km is not None else None}
