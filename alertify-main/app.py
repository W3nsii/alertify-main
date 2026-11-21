"""ALERTIFY: A Multi-Hazard Web-Based Disaster Preparedness Assistant (Batangas City).

Run:   python app.py            (http://127.0.0.1:5000)
Env:   SECRET_KEY, DATABASE_URL, ALERTIFY_ADMIN_EMAIL, ALERTIFY_ADMIN_PASSWORD,
       MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_SENDER
"""
import csv
import io
import json
import os
import re
import secrets
import smtplib
from collections import Counter
from datetime import timedelta
from email.message import EmailMessage
from functools import wraps
from urllib.parse import urlparse

from flask import (Flask, Response, abort, flash, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_

import engine
import seed_data
from icons import icon
from models import (AdminAccount, DisasterCategory, DisasterInstruction, DisasterReport,
                    EmergencyContact, EvacuationCenter, Notification, NotificationRead,
                    ReportHistory, User, db, utcnow)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Vercel runs the app as a serverless function: the project folder is read-only and
# only the temp folder (/tmp) is writable, and it is wiped between cold starts.
ON_VERCEL = bool(os.environ.get("VERCEL"))
if ON_VERCEL:
    import tempfile
    INSTANCE_DIR = os.path.join(tempfile.gettempdir(), "alertify-instance")
else:
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
LOCAL_DB = os.path.join(INSTANCE_DIR, "alertify.db")
SHARED_DB = os.path.join(BASE_DIR, "database", "alertify.db")  # snapshot kept in GitHub


def database_url():
    """External database URL, if one is configured (e.g. Postgres on Vercel/Neon).

    Vercel's Postgres integrations set POSTGRES_URL or DATABASE_URL as
    "postgres://..." or "postgresql://..."; SQLAlchemy needs the driver named.
    """
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url or None


def use_shared_database():
    """First run on a new computer: start from the shared snapshot in database/.

    This brings the same accounts, reports and admin changes to every copy.
    An existing local database is never overwritten.
    """
    if database_url() or os.path.exists(LOCAL_DB) or not os.path.exists(SHARED_DB):
        return
    import shutil
    shutil.copyfile(SHARED_DB, LOCAL_DB)
    print(f"[ALERTIFY] Started from the shared database: {SHARED_DB}", flush=True)


use_shared_database()
PH_OFFSET = timedelta(hours=8)  # Asia/Manila, no DST

REPORT_STATUSES = ["active", "acknowledged", "responding", "resolved", "closed"]
OPEN_STATUSES = ["active", "acknowledged", "responding"]
CENTER_OP_STATUSES = ["unknown", "open", "full", "closed"]
NOTIF_KINDS = ["advisory", "announcement", "reminder", "evacuation", "instruction_change"]
NOTIF_LEVELS = ["info", "advisory", "warning", "emergency"]
GUIDE_SECTIONS = [("before", "Before"), ("during", "During"), ("after", "After"),
                  ("checklist", "Preparedness checklist"), ("supplies", "Essential supplies"),
                  ("reminders", "Safety reminders"), ("avoid", "Things to avoid")]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _secret_key():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    if ON_VERCEL:
        # Each serverless instance would make its own key, so logins and forms would
        # randomly fail. Set SECRET_KEY in Vercel > Settings > Environment Variables.
        print("[ALERTIFY] WARNING: SECRET_KEY is not set on Vercel; logins may fail.", flush=True)
    path = os.path.join(INSTANCE_DIR, "secret_key")
    if not os.path.exists(path):
        with open(path, "w") as fh:
            fh.write(secrets.token_hex(32))
    with open(path) as fh:
        return fh.read().strip()


app = Flask(__name__, instance_path=INSTANCE_DIR)
app.config.update(
    SECRET_KEY=_secret_key(),
    SQLALCHEMY_DATABASE_URI=database_url() or "sqlite:///" + LOCAL_DB,
    # Serverless Postgres closes idle connections; check each one before use.
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_SECURE=ON_VERCEL,  # Vercel always serves over HTTPS
    REMEMBER_COOKIE_SECURE=ON_VERCEL,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,
)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))


# ------------------------------------------------------------------ helpers
def ph_time(dt, fmt="%b %d, %Y %I:%M %p"):
    return (dt + PH_OFFSET).strftime(fmt) if dt else "—"


app.jinja_env.filters["ph"] = ph_time
app.jinja_env.filters["from_json"] = lambda s: json.loads(s or "{}")
app.jinja_env.globals["icon"] = icon


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    session.permanent = True
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not token or not secrets.compare_digest(token, session.get("csrf", "")):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify(error="Your session expired. Please reload the page and try again."), 400
            flash("Your session expired. Please try again.", "error")
            return redirect(request.referrer or url_for("index"))


@app.after_request
def security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    # Send only our origin (never full URLs) to other sites. OpenStreetMap's tile
    # servers block map requests that arrive with no Referer at all.
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # Only ask for geolocation on our own origin.
    resp.headers.setdefault("Permissions-Policy", "geolocation=(self)")
    return resp


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*a, **kw):
        if not current_user.is_admin:
            abort(403)
        return fn(*a, **kw)
    return wrapper


def guest_token():
    if "guest_token" not in session:
        session["guest_token"] = secrets.token_urlsafe(24)
    return session["guest_token"]


def safe_next(target):
    if not target:
        return None
    p = urlparse(target)
    return target if not p.netloc and not p.scheme and target.startswith("/") else None


def claim_guest_reports(user):
    tok = session.get("guest_token")
    if not tok:
        return 0
    reports = DisasterReport.query.filter_by(guest_token=tok, user_id=None).all()
    for r in reports:
        r.user_id = user.id
        r.saved = True
        db.session.add(ReportHistory(report_id=r.id, event="claimed", actor_id=user.id,
                                     note="Report linked to account after sign-in."))
    db.session.commit()
    return len(reports)


def can_view_report(r):
    if current_user.is_authenticated and (current_user.is_admin or r.user_id == current_user.id):
        return True
    return r.user_id is None and r.guest_token and r.guest_token == session.get("guest_token")


def visible_notifications(limit=None):
    now = utcnow()
    qry = Notification.query.filter(Notification.active.is_(True),
                                    or_(Notification.expires_at.is_(None), Notification.expires_at > now))
    if current_user.is_authenticated and current_user.barangay:
        qry = qry.filter(or_(Notification.barangay.is_(None), Notification.barangay == "",
                             Notification.barangay == current_user.barangay))
    qry = qry.order_by(Notification.created_at.desc())
    return qry.limit(limit).all() if limit else qry.all()


def unread_ids(notes):
    ids = [n.id for n in notes]
    if not ids:
        return set()
    if current_user.is_authenticated:
        read = {r.notification_id for r in NotificationRead.query.filter(
            NotificationRead.user_id == current_user.id, NotificationRead.notification_id.in_(ids))}
        return set(ids) - read
    seen = session.get("notif_seen", 0)
    return {n.id for n in notes if n.id > seen}


@app.context_processor
def inject_globals():
    notes = visible_notifications(limit=8)
    return {
        "categories": DisasterCategory.query.filter_by(active=True).order_by(DisasterCategory.sort_order).all(),
        "primary_contacts": EmergencyContact.query.filter_by(active=True, is_primary=True)
        .order_by(EmergencyContact.sort_order).all(),
        "nav_notifications": notes,
        "nav_unread": unread_ids(notes),
        "severity_labels": engine.SEVERITY_LABELS,
        "setup_warning": setup_warning(),
    }


def setup_warning():
    """A message for the warning bar when the Vercel deployment is missing settings."""
    if not ON_VERCEL:
        return None
    if not os.environ.get("SECRET_KEY"):
        return ("Setup needed: add SECRET_KEY in Vercel > Settings > Environment Variables, then redeploy. "
                "Until then you may be logged out between pages.")
    if not database_url() and current_user.is_authenticated and current_user.is_admin:
        return ("No online database is connected, so new accounts, reports and changes are lost when "
                "Vercel restarts. Connect a Postgres database in Vercel > Storage, then redeploy.")
    return None


def send_email(to, subject, body):
    """Send via SMTP if configured. Returns True if sent."""
    server = os.environ.get("MAIL_SERVER")
    if not server:
        return False
    msg = EmailMessage()
    msg["Subject"], msg["To"] = subject, to
    msg["From"] = os.environ.get("MAIL_SENDER", os.environ.get("MAIL_USERNAME", "alertify@localhost"))
    msg.set_content(body)
    with smtplib.SMTP(server, int(os.environ.get("MAIL_PORT", 587))) as s:
        s.starttls()
        if os.environ.get("MAIL_USERNAME"):
            s.login(os.environ["MAIL_USERNAME"], os.environ.get("MAIL_PASSWORD", ""))
        s.send_message(msg)
    return True


def parse_float(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def parse_int(v, default=None):
    try:
        return int(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


def in_city(lat, lng):
    b = seed_data.CITY_BOUNDS
    return lat is not None and lng is not None and b["min_lat"] <= lat <= b["max_lat"] \
        and b["min_lng"] <= lng <= b["max_lng"]


# ------------------------------------------------------------------ public pages
@app.route("/")
def index():
    stats = {
        "centers": EvacuationCenter.query.filter_by(active=True).count(),
        "contacts": EmergencyContact.query.filter_by(active=True).count(),
        "barangays": len(seed_data.BARANGAYS),
    }
    return render_template("landing.html", stats=stats)


@app.route("/dashboard")
def dashboard():
    recent = []
    if current_user.is_authenticated:
        recent = current_user.reports.order_by(DisasterReport.created_at.desc()).limit(3).all()
    return render_template("dashboard.html", barangays=seed_data.BARANGAYS, recent=recent,
                           questions=engine.QUESTIONS, special=engine.SPECIAL_ASSISTANCE,
                           city_bounds=seed_data.CITY_BOUNDS, city_center=seed_data.CITY_CENTER,
                           center_count=EvacuationCenter.query.filter_by(active=True).count())


@app.route("/api/questions")
def api_questions():
    return jsonify(questions=engine.QUESTIONS, special=engine.SPECIAL_ASSISTANCE)


@app.route("/api/reports", methods=["POST"])
def api_create_report():
    data = request.get_json(silent=True) or {}
    errors = []
    cat = DisasterCategory.query.filter_by(code=str(data.get("category", "")), active=True).first()
    if not cat:
        return jsonify(error="Please select the disaster you are experiencing."), 400

    ans_errors, answers = engine.validate_answers(cat.code, data.get("answers") or {})
    errors += ans_errors
    valid_special = {k for k, _ in engine.SPECIAL_ASSISTANCE}
    special = [s for s in (data.get("special") or []) if s in valid_special]

    people = parse_int(data.get("people_count"), 1)
    if people is None or not 1 <= people <= 500:
        errors.append("Number of people must be between 1 and 500.")
    description = (data.get("description") or "").strip()[:1000]
    other_type = (data.get("other_type") or "").strip()[:120]
    if cat.code == "other" and other_type:
        answers["emergency_type"] = other_type

    barangay = (data.get("barangay") or "").strip()
    if barangay and barangay not in seed_data.BARANGAYS:
        errors.append("Please choose a barangay from the list.")
    lat, lng = parse_float(data.get("lat")), parse_float(data.get("lng"))
    if (lat is None) != (lng is None) or (lat is not None and not (-90 <= lat <= 90 and -180 <= lng <= 180)):
        errors.append("Location coordinates are invalid.")
        lat = lng = None
    if not barangay and lat is None:
        errors.append("Please share your location, pin it on the map, or select your barangay.")
    source = data.get("location_source") if data.get("location_source") in ("gps", "map_pin", "manual") else "manual"
    accuracy = parse_float(data.get("accuracy"))
    if errors:
        return jsonify(error=" ".join(errors), errors=errors), 400

    flags = engine.compute_flags(cat.code, answers, special)
    severity, score = engine.assess_severity(flags, people)
    instructions = engine.build_instructions(cat.code, flags)

    rec_center, rec_dist = None, None
    if lat is not None:
        near = engine.nearest_centers(lat, lng, hazard=cat.code, limit=1)
        if near:
            rec_center, rec_dist = near[0][0], round(near[0][1], 2)
    elif barangay:
        rec_center = EvacuationCenter.query.filter_by(active=True, barangay=barangay).first()

    labels = {s["key"]: s for s in engine.QUESTIONS.get(cat.code, [])}
    readable = []
    for k, v in answers.items():
        qd = labels.get(k)
        if qd:
            opt = next((o["label"] for o in qd["options"] if o["value"] == v), v)
            readable.append({"q": qd["label"], "a": opt})
        elif k == "emergency_type":
            readable.append({"q": "Type of emergency", "a": v})

    report = DisasterReport(
        reference="ALR-" + secrets.token_hex(3).upper(),
        user_id=current_user.id if current_user.is_authenticated else None,
        guest_token=None if current_user.is_authenticated else guest_token(),
        category_id=cat.id, answers_json=json.dumps(answers), barangay=barangay or None,
        latitude=lat, longitude=lng, location_accuracy=accuracy, location_source=source,
        people_count=people,
        special_assistance=",".join(special) or None, description=description or None,
        severity=severity, severity_score=score, flags=",".join(sorted(flags)),
        instructions_json=json.dumps({"sections": instructions, "answers": readable,
                                      "immediate_danger": engine.immediate_danger(flags),
                                      "outside_city": lat is not None and not in_city(lat, lng)}),
        recommended_center_id=rec_center.id if rec_center else None,
        recommended_distance_km=rec_dist,
        saved=current_user.is_authenticated,
    )
    db.session.add(report)
    db.session.flush()
    db.session.add(ReportHistory(report_id=report.id, event="created", new_status="active",
                                 actor_id=current_user.id if current_user.is_authenticated else None,
                                 note=f"Report submitted ({engine.SEVERITY_LABELS[severity]} severity)."))
    db.session.commit()
    return jsonify(ok=True, reference=report.reference,
                   redirect=url_for("report_result", ref=report.reference))


@app.route("/report/<ref>")
def report_result(ref):
    r = DisasterReport.query.filter_by(reference=ref).first_or_404()
    if not can_view_report(r):
        abort(404)
    nearby = []
    if r.latitude is not None:
        nearby = engine.nearest_centers(r.latitude, r.longitude, hazard=r.category.code, limit=5)
    return render_template("report_result.html", r=r, data=r.instructions, sections=engine.SECTIONS,
                           nearby=nearby, special_labels=dict(engine.SPECIAL_ASSISTANCE))


@app.route("/report/<ref>/save", methods=["POST"])
def report_save(ref):
    r = DisasterReport.query.filter_by(reference=ref).first_or_404()
    if not can_view_report(r):
        abort(404)
    if not current_user.is_authenticated:
        flash("Log in or create an account to save this report to your history. "
              "It will be linked automatically.", "info")
        return redirect(url_for("login", next=url_for("report_result", ref=ref)))
    if r.user_id is None:
        r.user_id = current_user.id
    if not r.saved:
        r.saved = True
        db.session.add(ReportHistory(report_id=r.id, event="saved", actor_id=current_user.id,
                                     note="Saved to My Disaster History."))
    db.session.commit()
    flash("Report saved to My Disaster History.", "success")
    return redirect(url_for("history_detail", ref=ref))


@app.route("/guide")
def guide():
    return render_template("guide.html", guide=load_guide(), sections=GUIDE_SECTIONS, active_code=None)


@app.route("/guide/<code>")
def guide_detail(code):
    cat = DisasterCategory.query.filter_by(code=code).first_or_404()
    if code == "other":
        return redirect(url_for("guide"))
    return render_template("guide.html", guide=load_guide(), sections=GUIDE_SECTIONS, active_code=code,
                           active_cat=cat)


def load_guide():
    rows = (DisasterInstruction.query.filter_by(context="guide", active=True)
            .order_by(DisasterInstruction.priority, DisasterInstruction.id).all())
    out = {}
    for r in rows:
        out.setdefault(r.disaster, {}).setdefault(r.section, []).append(r)
    return out


@app.route("/evacuation-centers")
def evacuation_centers():
    barangays = sorted({c.barangay for c in EvacuationCenter.query.filter_by(active=True) if c.barangay})
    return render_template("evacuation.html", barangays=barangays, all_barangays=seed_data.BARANGAYS,
                           city_center=seed_data.CITY_CENTER,
                           hazard=request.args.get("hazard", ""), focus=request.args.get("center", ""),
                           ulat=request.args.get("lat", ""), ulng=request.args.get("lng", ""))


@app.route("/api/centers")
def api_centers():
    qry = EvacuationCenter.query.filter_by(active=True)
    brgy = request.args.get("barangay")
    if brgy:
        qry = qry.filter_by(barangay=brgy)
    centers = qry.order_by(EvacuationCenter.name).all()
    hazard = request.args.get("hazard")
    lat, lng = parse_float(request.args.get("lat")), parse_float(request.args.get("lng"))
    out = []
    for c in centers:
        d = c.to_dict()
        d["suitable"] = bool(hazard) and hazard in c.hazard_list
        d["distance_km"] = round(engine.haversine_km(lat, lng, c.latitude, c.longitude), 2) \
            if lat is not None and lng is not None and c.latitude is not None else None
        out.append(d)
    if lat is not None:
        out.sort(key=lambda d: (d["distance_km"] is None, d["distance_km"] or 0))
    verified_for_hazard = any(d["suitable"] for d in out)
    return jsonify(centers=out, hazard=hazard, hazard_data_available=verified_for_hazard,
                   source=seed_data.SOURCE_PDF)


def barangay_location(barangay):
    """Approximate a barangay's position as the average of its evacuation centers.

    Returns (lat, lng) or None when the barangay has no mapped center, in which
    case the user is asked to pin their location or use GPS instead.
    """
    pts = [(c.latitude, c.longitude) for c in
           EvacuationCenter.query.filter_by(active=True, barangay=barangay)
           if c.latitude is not None]
    if not pts:
        return None
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


@app.route("/api/safety-plan")
def api_safety_plan():
    """Nearest evacuation centers + what to do, for a typed, pinned, or GPS location."""
    hazard = (request.args.get("hazard") or "").strip()
    if hazard and not DisasterCategory.query.filter_by(code=hazard, active=True).first():
        return jsonify(error="Please choose a valid disaster type."), 400
    stage = request.args.get("stage", "prepare")
    if stage not in engine.PLAN_STAGES:
        return jsonify(error="Please choose whether you are preparing or it is happening now."), 400

    lat, lng = parse_float(request.args.get("lat")), parse_float(request.args.get("lng"))
    barangay = (request.args.get("barangay") or "").strip()
    approximate = False
    if lat is not None or lng is not None:
        if lat is None or lng is None or not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return jsonify(error="Location coordinates are invalid."), 400
        label = "Your pinned / GPS location"
    elif barangay:
        match = next((b for b in seed_data.BARANGAYS if b.lower() == barangay.lower()), None)
        if not match:
            return jsonify(error=f'"{barangay}" is not a Batangas City barangay. '
                                 "Pick one from the suggestions list."), 400
        point = barangay_location(match)
        if point is None:
            return jsonify(error=f"We don't have a mapped center in {match} yet to estimate your position. "
                                 "Tap the map where you are, or use GPS."), 422
        lat, lng = point
        label, approximate = f"Brgy. {match} (approximate)", True
    else:
        return jsonify(error="Enter your barangay, tap your location on the map, or use GPS."), 400

    plan = engine.safety_plan(lat, lng, hazard, stage)
    plan.update(origin={"lat": lat, "lng": lng, "label": label, "approximate": approximate},
                outside_city=not in_city(lat, lng), hazard=hazard, stage=stage)
    return jsonify(plan)


@app.route("/contacts")
def contacts():
    rows = EmergencyContact.query.filter_by(active=True).order_by(EmergencyContact.sort_order).all()
    grouped = {}
    for c in rows:
        grouped.setdefault(c.category, []).append(c)
    return render_template("contacts.html", grouped=grouped)


@app.route("/api/contacts")
def api_contacts():
    rows = EmergencyContact.query.filter_by(active=True).order_by(EmergencyContact.sort_order).all()
    return jsonify(contacts=[c.to_dict() for c in rows])


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/offline")
def offline():
    return render_template("offline.html")


@app.route("/sw.js")
def service_worker():
    resp = send_from_directory(os.path.join(BASE_DIR, "static", "js"), "sw.js")
    resp.headers["Content-Type"] = "application/javascript"
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


# ------------------------------------------------------------------ history
@app.route("/history")
@login_required
def history():
    qry = DisasterReport.query.filter_by(user_id=current_user.id)
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "")
    dfrom, dto = request.args.get("from", ""), request.args.get("to", "")
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(DisasterReport.reference.ilike(like), DisasterReport.barangay.ilike(like),
                             DisasterReport.description.ilike(like)))
    if cat:
        qry = qry.join(DisasterCategory).filter(DisasterCategory.code == cat)
    from datetime import datetime
    try:
        if dfrom:
            qry = qry.filter(DisasterReport.created_at >= datetime.strptime(dfrom, "%Y-%m-%d") - PH_OFFSET)
        if dto:
            qry = qry.filter(DisasterReport.created_at < datetime.strptime(dto, "%Y-%m-%d") - PH_OFFSET + timedelta(days=1))
    except ValueError:
        flash("Invalid date filter.", "error")
    reports = qry.order_by(DisasterReport.created_at.desc()).all()
    return render_template("history.html", reports=reports, q=q, cat=cat, dfrom=dfrom, dto=dto)


@app.route("/history/<ref>")
@login_required
def history_detail(ref):
    r = DisasterReport.query.filter_by(reference=ref, user_id=current_user.id).first_or_404()
    return render_template("history_detail.html", r=r, data=r.instructions, sections=engine.SECTIONS,
                           special_labels=dict(engine.SPECIAL_ASSISTANCE))


# ------------------------------------------------------------------ notifications
@app.route("/notifications")
def notifications():
    notes = visible_notifications()
    unread = unread_ids(notes)
    return render_template("notifications.html", notes=notes, unread=unread)


@app.route("/notifications/read-all", methods=["POST"])
def notifications_read_all():
    notes = visible_notifications()
    if current_user.is_authenticated:
        for nid in unread_ids(notes):
            db.session.add(NotificationRead(notification_id=nid, user_id=current_user.id))
        db.session.commit()
    elif notes:
        session["notif_seen"] = max(n.id for n in notes)
    if request.is_json or request.headers.get("X-CSRF-Token"):
        return jsonify(ok=True)
    return redirect(request.referrer or url_for("notifications"))


# ------------------------------------------------------------------ auth
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = {}
    if request.method == "POST":
        form = request.form
        name = form.get("full_name", "").strip()
        email = form.get("email", "").strip().lower()
        phone = form.get("phone", "").strip()
        brgy = form.get("barangay", "").strip()
        pw, pw2 = form.get("password", ""), form.get("password2", "")
        errs = []
        if len(name) < 2:
            errs.append("Please enter your full name.")
        if not EMAIL_RE.match(email):
            errs.append("Please enter a valid email address.")
        elif User.query.filter_by(email=email).first():
            errs.append("An account with this email already exists.")
        if phone and not re.fullmatch(r"[0-9+()\-\s]{7,20}", phone):
            errs.append("Please enter a valid phone number.")
        if brgy and brgy not in seed_data.BARANGAYS:
            errs.append("Please choose a barangay from the list.")
        if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
            errs.append("Password must be at least 8 characters and include letters and numbers.")
        if pw != pw2:
            errs.append("Passwords do not match.")
        if errs:
            for e in errs:
                flash(e, "error")
        else:
            u = User(full_name=name, email=email, phone=phone or None, barangay=brgy or None)
            u.set_password(pw)
            u.last_login = utcnow()
            db.session.add(u)
            db.session.commit()
            login_user(u)
            n = claim_guest_reports(u)
            flash("Welcome to ALERTIFY! Your account has been created."
                  + (f" {n} earlier report(s) were saved to your history." if n else ""), "success")
            return redirect(safe_next(request.args.get("next")) or url_for("dashboard"))
    return render_template("auth/register.html", barangays=seed_data.BARANGAYS, form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        u = User.query.filter_by(email=email).first()
        if u and u.check_password(request.form.get("password", "")):
            if not u.is_active_account:
                flash("This account has been deactivated. Please contact the administrator.", "error")
            else:
                login_user(u, remember=bool(request.form.get("remember")))
                u.last_login = utcnow()
                db.session.commit()
                n = claim_guest_reports(u)
                flash(f"Welcome back, {u.full_name.split()[0]}!"
                      + (f" {n} report(s) were saved to your history." if n else ""), "success")
                dest = safe_next(request.args.get("next"))
                return redirect(dest or (url_for("admin_overview") if u.is_admin else url_for("dashboard")))
        else:
            flash("Incorrect email or password.", "error")
    return render_template("auth/login.html")


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    session.pop("guest_token", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        u = User.query.filter_by(email=email).first()
        if u:
            u.reset_token = secrets.token_urlsafe(32)
            u.reset_expires = utcnow() + timedelta(hours=1)
            db.session.commit()
            link = url_for("reset_password", token=u.reset_token, _external=True)
            body = f"Hello {u.full_name},\n\nReset your ALERTIFY password using this link (valid for 1 hour):\n{link}\n\nIf you did not request this, ignore this email."
            try:
                sent = send_email(u.email, "ALERTIFY password reset", body)
            except Exception as exc:  # noqa: BLE001
                app.logger.error("Email sending failed: %s", exc)
                sent = False
            if not sent:
                # No SMTP configured: development fallback — print link to server console only.
                print(f"\n[ALERTIFY] Password reset link for {u.email}: {link}\n", flush=True)
        flash("If an account exists for that email, a password reset link has been sent. "
              "(If email is not configured on this server, the administrator can find the link in the server console.)",
              "info")
        return redirect(url_for("login"))
    return render_template("auth/forgot.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    u = User.query.filter_by(reset_token=token).first()
    if not u or not u.reset_expires or u.reset_expires < utcnow():
        flash("This reset link is invalid or has expired.", "error")
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        pw, pw2 = request.form.get("password", ""), request.form.get("password2", "")
        if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
            flash("Password must be at least 8 characters and include letters and numbers.", "error")
        elif pw != pw2:
            flash("Passwords do not match.", "error")
        else:
            u.set_password(pw)
            u.reset_token = u.reset_expires = None
            db.session.commit()
            flash("Your password has been reset. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("auth/reset.html", token=token)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "info":
            name = request.form.get("full_name", "").strip()
            phone = request.form.get("phone", "").strip()
            brgy = request.form.get("barangay", "").strip()
            if len(name) < 2:
                flash("Please enter your full name.", "error")
            elif phone and not re.fullmatch(r"[0-9+()\-\s]{7,20}", phone):
                flash("Please enter a valid phone number.", "error")
            elif brgy and brgy not in seed_data.BARANGAYS:
                flash("Please choose a barangay from the list.", "error")
            else:
                current_user.full_name, current_user.phone = name, phone or None
                current_user.barangay = brgy or None
                db.session.commit()
                flash("Profile updated.", "success")
        elif action == "password":
            cur, pw, pw2 = (request.form.get(k, "") for k in ("current", "password", "password2"))
            if not current_user.check_password(cur):
                flash("Current password is incorrect.", "error")
            elif len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
                flash("New password must be at least 8 characters and include letters and numbers.", "error")
            elif pw != pw2:
                flash("New passwords do not match.", "error")
            else:
                current_user.set_password(pw)
                db.session.commit()
                flash("Password changed.", "success")
        return redirect(url_for("profile"))
    stats = {
        "total": current_user.reports.count(),
        "open": current_user.reports.filter(DisasterReport.status.in_(OPEN_STATUSES)).count(),
    }
    return render_template("profile.html", barangays=seed_data.BARANGAYS, stats=stats)


# ================================================================== ADMIN
@app.route("/admin")
@admin_required
def admin_overview():
    by_cat = dict(db.session.query(DisasterCategory.name, func.count(DisasterReport.id))
                  .outerjoin(DisasterReport, DisasterReport.category_id == DisasterCategory.id)
                  .group_by(DisasterCategory.name).all())
    by_brgy = (db.session.query(DisasterReport.barangay, func.count(DisasterReport.id))
               .filter(DisasterReport.barangay.isnot(None)).group_by(DisasterReport.barangay)
               .order_by(func.count(DisasterReport.id).desc()).limit(10).all())
    by_sev = dict(db.session.query(DisasterReport.severity, func.count(DisasterReport.id))
                  .group_by(DisasterReport.severity).all())
    since = utcnow() - timedelta(days=13)
    days = Counter(((r.created_at + PH_OFFSET).strftime("%b %d"))
                   for r in DisasterReport.query.filter(DisasterReport.created_at >= since))
    today = utcnow() + PH_OFFSET
    trend = [((today - timedelta(days=i)).strftime("%b %d")) for i in range(13, -1, -1)]
    stats = {
        "users": User.query.count(),
        "reports": DisasterReport.query.count(),
        "active": DisasterReport.query.filter(DisasterReport.status.in_(OPEN_STATUSES)).count(),
        "critical": DisasterReport.query.filter(DisasterReport.status.in_(OPEN_STATUSES),
                                                DisasterReport.severity == "critical").count(),
        "centers": EvacuationCenter.query.count(),
        "centers_verified": EvacuationCenter.query.filter_by(verified=True).count(),
        "contacts_unverified": EmergencyContact.query.filter_by(verified=False, active=True).count(),
    }
    recent = DisasterReport.query.order_by(DisasterReport.created_at.desc()).limit(8).all()
    return render_template("admin/overview.html", stats=stats, recent=recent,
                           chart=dict(cat_labels=list(by_cat.keys()), cat_values=list(by_cat.values()),
                                      brgy_labels=[b for b, _ in by_brgy], brgy_values=[n for _, n in by_brgy],
                                      sev=[by_sev.get(s, 0) for s in ("low", "moderate", "high", "critical")],
                                      trend_labels=trend, trend_values=[days.get(d, 0) for d in trend]))


def filtered_reports():
    qry = DisasterReport.query
    a = request.args
    if a.get("category"):
        qry = qry.join(DisasterCategory).filter(DisasterCategory.code == a["category"])
    if a.get("barangay"):
        qry = qry.filter(DisasterReport.barangay == a["barangay"])
    if a.get("status") == "open":
        qry = qry.filter(DisasterReport.status.in_(OPEN_STATUSES))
    elif a.get("status"):
        qry = qry.filter(DisasterReport.status == a["status"])
    if a.get("severity"):
        qry = qry.filter(DisasterReport.severity == a["severity"])
    if a.get("q"):
        like = f"%{a['q'].strip()}%"
        qry = qry.outerjoin(User, DisasterReport.user_id == User.id).filter(
            or_(DisasterReport.reference.ilike(like), DisasterReport.description.ilike(like),
                User.full_name.ilike(like)))
    return qry.order_by(DisasterReport.created_at.desc())


@app.route("/admin/reports")
@admin_required
def admin_reports():
    reports = filtered_reports().limit(300).all()
    brgys = sorted({b for (b,) in db.session.query(DisasterReport.barangay).distinct() if b})
    pins = [{"ref": r.reference, "lat": r.latitude, "lng": r.longitude, "sev": r.severity,
             "cat": r.category.name, "status": r.status} for r in reports if r.latitude is not None]
    return render_template("admin/reports.html", reports=reports, barangays=brgys, statuses=REPORT_STATUSES,
                           pins=pins, args=request.args, city_center=seed_data.CITY_CENTER)


@app.route("/admin/reports/export.csv")
@admin_required
def admin_reports_export():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Reference", "Submitted (PHT)", "Disaster", "Severity", "Score", "Status", "Barangay",
                "Latitude", "Longitude", "Location source", "People", "Special assistance", "Description",
                "Reporter", "Recommended center", "Distance km"])
    for r in filtered_reports().all():
        w.writerow([r.reference, ph_time(r.created_at, "%Y-%m-%d %H:%M"), r.category.name, r.severity,
                    r.severity_score, r.status, r.barangay or "", r.latitude or "", r.longitude or "",
                    r.location_source or "", r.people_count, r.special_assistance or "",
                    (r.description or "").replace("\n", " "), r.user.full_name if r.user else "Guest",
                    r.recommended_center.name if r.recommended_center else "", r.recommended_distance_km or ""])
    return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=alertify-reports-{(utcnow() + PH_OFFSET):%Y%m%d-%H%M}.csv"})


@app.route("/admin/reports/<int:rid>", methods=["GET", "POST"])
@admin_required
def admin_report_detail(rid):
    r = db.get_or_404(DisasterReport, rid)
    if request.method == "POST":
        new = request.form.get("status")
        note = request.form.get("note", "").strip()[:500]
        if new not in REPORT_STATUSES:
            flash("Invalid status.", "error")
        else:
            if new != r.status or note:
                db.session.add(ReportHistory(report_id=r.id, event="status_change" if new != r.status else "note",
                                             old_status=r.status, new_status=new, note=note or None,
                                             actor_id=current_user.id))
                r.status = new
                db.session.commit()
                flash("Report updated.", "success")
        return redirect(url_for("admin_report_detail", rid=rid))
    return render_template("admin/report_detail.html", r=r, data=r.instructions, sections=engine.SECTIONS,
                           statuses=REPORT_STATUSES, special_labels=dict(engine.SPECIAL_ASSISTANCE))


# ---- evacuation centers
@app.route("/admin/centers")
@admin_required
def admin_centers():
    qry = EvacuationCenter.query
    f = request.args.get("filter", "")
    if f == "pending":
        qry = qry.filter_by(verified=False)
    elif f == "verified":
        qry = qry.filter_by(verified=True)
    elif f == "inactive":
        qry = qry.filter_by(active=False)
    if request.args.get("q"):
        like = f"%{request.args['q']}%"
        qry = qry.filter(or_(EvacuationCenter.name.ilike(like), EvacuationCenter.barangay.ilike(like)))
    return render_template("admin/centers.html", centers=qry.order_by(EvacuationCenter.name).all(),
                           f=f, q=request.args.get("q", ""))


@app.route("/admin/centers/new", methods=["GET", "POST"])
@app.route("/admin/centers/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def admin_center_form(cid=None):
    c = db.get_or_404(EvacuationCenter, cid) if cid else EvacuationCenter(active=True, source="Administrator entry")
    if request.method == "POST":
        f = request.form
        name = f.get("name", "").strip()
        lat, lng = parse_float(f.get("latitude")), parse_float(f.get("longitude"))
        errs = []
        if len(name) < 3:
            errs.append("Name is required.")
        if (lat is None) != (lng is None):
            errs.append("Provide both latitude and longitude, or neither.")
        elif lat is not None and not in_city(lat, lng):
            errs.append("Coordinates must be within Batangas City.")
        fam, per = parse_int(f.get("capacity_families")), parse_int(f.get("capacity_persons"))
        if (fam is not None and fam < 0) or (per is not None and per < 0):
            errs.append("Capacity cannot be negative.")
        op = f.get("operational_status", "unknown")
        if op not in CENTER_OP_STATUSES:
            errs.append("Invalid operational status.")
        if errs:
            for e in errs:
                flash(e, "error")
        else:
            c.name, c.location = name, f.get("location", "").strip() or None
            c.barangay = f.get("barangay", "").strip() or None
            c.capacity_families, c.capacity_persons = fam, per
            c.latitude, c.longitude = lat, lng
            c.source_note = f.get("source_note", "").strip() or None
            if f.get("source"):
                c.source = f.get("source").strip()
            hz = [h for h in f.getlist("hazards") if h in {k for k, *_ in seed_data.CATEGORIES}]
            c.hazards = ",".join(hz)
            if op != c.operational_status:
                c.operational_status, c.status_updated_at = op, utcnow()
            c.active = bool(f.get("active"))
            want_verified = bool(f.get("verified"))
            if want_verified and not c.verified:
                c.verified, c.verified_at, c.verified_by = True, utcnow(), current_user.id
            elif not want_verified:
                c.verified, c.verified_at, c.verified_by = False, None, None
            db.session.add(c)
            db.session.commit()
            flash("Evacuation center saved.", "success")
            return redirect(url_for("admin_centers"))
    return render_template("admin/center_form.html", c=c, op_statuses=CENTER_OP_STATUSES,
                           barangays=seed_data.BARANGAYS, city_center=seed_data.CITY_CENTER)


@app.route("/admin/centers/<int:cid>/<action>", methods=["POST"])
@admin_required
def admin_center_action(cid, action):
    c = db.get_or_404(EvacuationCenter, cid)
    if action == "toggle":
        c.active = not c.active
    elif action == "verify":
        c.verified, c.verified_at, c.verified_by = True, utcnow(), current_user.id
    elif action == "unverify":
        c.verified, c.verified_at, c.verified_by = False, None, None
    else:
        abort(400)
    db.session.commit()
    flash(f"{c.name}: updated.", "success")
    return redirect(request.referrer or url_for("admin_centers"))


# ---- emergency contacts
@app.route("/admin/contacts")
@admin_required
def admin_contacts():
    rows = EmergencyContact.query.order_by(EmergencyContact.category, EmergencyContact.sort_order).all()
    return render_template("admin/contacts.html", contacts=rows)


@app.route("/admin/contacts/new", methods=["GET", "POST"])
@app.route("/admin/contacts/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def admin_contact_form(cid=None):
    c = db.get_or_404(EmergencyContact, cid) if cid else EmergencyContact(active=True)
    cats = sorted({x.category for x in EmergencyContact.query})
    if request.method == "POST":
        f = request.form
        org, cat, nums = f.get("organization", "").strip(), f.get("category", "").strip(), f.get("numbers", "").strip()
        if not org or not cat or not nums:
            flash("Organization, category and at least one number are required.", "error")
        elif not re.fullmatch(r"[0-9+()\-\s/–]{3,255}", nums):
            flash("Numbers may contain digits, spaces, ( ) + - and use / to separate multiple numbers.", "error")
        else:
            c.organization, c.category, c.numbers = org, cat, nums
            c.description = f.get("description", "").strip() or None
            c.sort_order = parse_int(f.get("sort_order"), 0)
            c.is_primary, c.active = bool(f.get("is_primary")), bool(f.get("active"))
            v = bool(f.get("verified"))
            if v and not c.verified:
                c.verified_at = utcnow()
            c.verified = v
            db.session.add(c)
            db.session.commit()
            flash("Contact saved.", "success")
            return redirect(url_for("admin_contacts"))
    return render_template("admin/contact_form.html", c=c, cats=cats)


@app.route("/admin/contacts/<int:cid>/<action>", methods=["POST"])
@admin_required
def admin_contact_action(cid, action):
    c = db.get_or_404(EmergencyContact, cid)
    if action == "toggle":
        c.active = not c.active
    elif action == "verify":
        c.verified, c.verified_at = True, utcnow()
    elif action == "delete":
        db.session.delete(c)
    else:
        abort(400)
    db.session.commit()
    flash("Contact updated.", "success")
    return redirect(url_for("admin_contacts"))


# ---- instructions
@app.route("/admin/instructions")
@admin_required
def admin_instructions():
    ctx = request.args.get("context", "response")
    dis = request.args.get("disaster", "")
    qry = DisasterInstruction.query.filter_by(context=ctx)
    if dis:
        qry = qry.filter_by(disaster=dis)
    rows = qry.order_by(DisasterInstruction.disaster, DisasterInstruction.section,
                        DisasterInstruction.priority).all()
    return render_template("admin/instructions.html", rows=rows, ctx=ctx, dis=dis)


def instruction_choices():
    conditions = sorted({"base", "trapped", "injured", "vulnerable", *engine.WEIGHTS.keys()})
    return {
        "disasters": ["general"] + [c for c, *_ in seed_data.CATEGORIES],
        "response_sections": [s for s, _ in engine.SECTIONS],
        "guide_sections": [s for s, _ in GUIDE_SECTIONS],
        "conditions": conditions,
    }


@app.route("/admin/instructions/new", methods=["GET", "POST"])
@app.route("/admin/instructions/<int:iid>/edit", methods=["GET", "POST"])
@admin_required
def admin_instruction_form(iid=None):
    row = db.get_or_404(DisasterInstruction, iid) if iid else DisasterInstruction(
        context=request.args.get("context", "response"), active=True, condition="base", priority=50)
    ch = instruction_choices()
    if request.method == "POST":
        f = request.form
        ctx = f.get("context")
        sec = f.get("section")
        dis = f.get("disaster")
        cond = f.get("condition", "base") if ctx == "response" else "base"
        text = f.get("text", "").strip()
        valid_secs = ch["response_sections"] if ctx == "response" else ch["guide_sections"]
        if ctx not in ("response", "guide") or sec not in valid_secs or dis not in ch["disasters"] \
                or cond not in ch["conditions"] or len(text) < 5:
            flash("Please complete all fields with valid values.", "error")
        else:
            changed = row.id is not None and row.text != text
            row.context, row.section, row.disaster, row.condition, row.text = ctx, sec, dis, cond, text
            row.priority = parse_int(f.get("priority"), 50)
            row.source = f.get("source", "").strip() or None
            row.active = bool(f.get("active"))
            db.session.add(row)
            if f.get("announce"):
                db.session.add(Notification(
                    title=f"Updated {dis} guidance", kind="instruction_change", level="info",
                    body=("Emergency instructions have been " + ("updated" if changed else "added") + f": {text[:200]}"),
                    source=row.source or "ALERTIFY administrator", created_by=current_user.id))
            db.session.commit()
            flash("Instruction saved. New reports and the Disaster Guide now use this text.", "success")
            return redirect(url_for("admin_instructions", context=ctx, disaster=dis))
    return render_template("admin/instruction_form.html", row=row, ch=ch)


@app.route("/admin/instructions/<int:iid>/<action>", methods=["POST"])
@admin_required
def admin_instruction_action(iid, action):
    row = db.get_or_404(DisasterInstruction, iid)
    ctx = row.context
    if action == "toggle":
        row.active = not row.active
    elif action == "delete":
        db.session.delete(row)
    else:
        abort(400)
    db.session.commit()
    flash("Instruction updated.", "success")
    return redirect(url_for("admin_instructions", context=ctx))


# ---- users
@app.route("/admin/users")
@admin_required
def admin_users():
    q = request.args.get("q", "").strip()
    qry = User.query
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(User.full_name.ilike(like), User.email.ilike(like)))
    users = qry.order_by(User.created_at.desc()).all()
    counts = dict(db.session.query(DisasterReport.user_id, func.count(DisasterReport.id))
                  .group_by(DisasterReport.user_id).all())
    return render_template("admin/users.html", users=users, counts=counts, q=q)


@app.route("/admin/users/<int:uid>/<action>", methods=["POST"])
@admin_required
def admin_user_action(uid, action):
    u = db.get_or_404(User, uid)
    if u.id == current_user.id:
        flash("You cannot change your own access here.", "error")
        return redirect(url_for("admin_users"))
    if action == "toggle":
        u.is_active_account = not u.is_active_account
    elif action == "make_admin":
        if not u.admin_account:
            db.session.add(AdminAccount(user_id=u.id, granted_by=current_user.id))
        else:
            u.admin_account.active = True
    elif action == "revoke_admin" and u.admin_account:
        u.admin_account.active = False
    else:
        abort(400)
    db.session.commit()
    flash(f"{u.full_name}: access updated.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:uid>")
@admin_required
def admin_user_detail(uid):
    u = db.get_or_404(User, uid)
    return render_template("admin/user_detail.html", u=u,
                           reports=u.reports.order_by(DisasterReport.created_at.desc()).all())


# ---- notifications
@app.route("/admin/notifications", methods=["GET", "POST"])
@admin_required
def admin_notifications():
    if request.method == "POST":
        f = request.form
        title, body = f.get("title", "").strip(), f.get("body", "").strip()
        kind, level = f.get("kind"), f.get("level")
        brgy = f.get("barangay", "").strip()
        hours = parse_int(f.get("expires_hours"))
        if not title or not body or kind not in NOTIF_KINDS or level not in NOTIF_LEVELS:
            flash("Title, message, type and level are required.", "error")
        elif brgy and brgy not in seed_data.BARANGAYS:
            flash("Invalid barangay.", "error")
        else:
            db.session.add(Notification(
                title=title[:160], body=body[:4000], kind=kind, level=level,
                source=f.get("source", "").strip()[:160] or None, barangay=brgy or None,
                created_by=current_user.id,
                expires_at=utcnow() + timedelta(hours=hours) if hours and hours > 0 else None))
            db.session.commit()
            flash("Announcement published.", "success")
        return redirect(url_for("admin_notifications"))
    rows = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template("admin/notifications.html", rows=rows, kinds=NOTIF_KINDS, levels=NOTIF_LEVELS,
                           barangays=seed_data.BARANGAYS, now=utcnow())


@app.route("/admin/notifications/<int:nid>/toggle", methods=["POST"])
@admin_required
def admin_notification_toggle(nid):
    n = db.get_or_404(Notification, nid)
    n.active = not n.active
    db.session.commit()
    return redirect(url_for("admin_notifications"))


# ------------------------------------------------------------------ errors
@app.errorhandler(403)
def e403(_):
    return render_template("error.html", code=403, msg="You do not have permission to view this page."), 403


@app.errorhandler(404)
def e404(_):
    return render_template("error.html", code=404, msg="The page you are looking for could not be found."), 404


# ------------------------------------------------------------------ seeding
def import_shared_snapshot():
    """Empty external database (e.g. Postgres on Vercel): copy in database/alertify.db.

    This gives a new online database the same accounts, reports and admin
    changes as the shared snapshot, so the usual logins work right away.
    Runs only once: it does nothing if the database already has users.
    """
    if not database_url() or not os.path.exists(SHARED_DB) or User.query.first():
        return
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError
    source = create_engine("sqlite:///" + SHARED_DB)
    try:
        with source.connect() as src:
            for table in db.metadata.sorted_tables:          # parents before children
                rows = [dict(r._mapping) for r in src.execute(table.select())]
                if rows:
                    db.session.execute(table.insert(), rows)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()   # another server imported it at the same moment
        return
    finally:
        source.dispose()
    if db.engine.dialect.name == "postgresql":
        # Copied rows keep their ids; move each id counter past them.
        for table in db.metadata.sorted_tables:
            if "id" in table.c:
                db.session.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table.name}), 1))"))
        db.session.commit()
    print("[ALERTIFY] Imported accounts and data from the shared database.", flush=True)


def seed_database():
    db.create_all()
    import_shared_snapshot()
    if not DisasterCategory.query.first():
        for i, (code, name, icon, desc) in enumerate(seed_data.CATEGORIES):
            db.session.add(DisasterCategory(code=code, name=name, icon=icon, description=desc, sort_order=i))
    if not EvacuationCenter.query.first():
        for (name, loc, brgy, fam, per, lng, lat, note) in seed_data.EVACUATION_CENTERS:
            db.session.add(EvacuationCenter(
                name=name, location=loc, barangay=brgy, capacity_families=fam, capacity_persons=per,
                latitude=lat, longitude=lng, source=seed_data.SOURCE_PDF,
                source_note=note or "Imported from source PDF — pending administrator verification.",
                verified=False, hazards="", operational_status="unknown"))
    if not EmergencyContact.query.first():
        for i, (org, cat, nums, desc, primary) in enumerate(seed_data.CONTACTS):
            db.session.add(EmergencyContact(organization=org, category=cat, numbers=nums, description=desc,
                                            is_primary=primary, sort_order=i, verified=False))
    if not DisasterInstruction.query.first():
        for (dis, sec, cond, text, prio) in seed_data.RESPONSE_INSTRUCTIONS:
            db.session.add(DisasterInstruction(disaster=dis, context="response", section=sec, condition=cond,
                                               text=text, priority=prio, source=seed_data.GUIDANCE_SRC))
        for dis, secs in seed_data.GUIDE.items():
            for sec, items in secs.items():
                for i, text in enumerate(items):
                    db.session.add(DisasterInstruction(disaster=dis, context="guide", section=sec, condition="base",
                                                       text=text, priority=i, source=seed_data.GUIDANCE_SRC))
    if not Notification.query.first():
        db.session.add(Notification(
            title="Prepare your go-bag before the rainy season",
            body="Pack water, food, medicines, a flashlight, a power bank, and copies of important documents. "
                 "Check the Disaster Guide for a full checklist.",
            kind="reminder", level="info", source="ALERTIFY safety reminder (not an official advisory)"))
    db.session.commit()

    if not AdminAccount.query.first():
        email = os.environ.get("ALERTIFY_ADMIN_EMAIL", "admin@alertify.local").lower()
        pw = os.environ.get("ALERTIFY_ADMIN_PASSWORD") or secrets.token_urlsafe(10)
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(full_name="ALERTIFY Administrator", email=email)
            u.set_password(pw)
            db.session.add(u)
            db.session.flush()
        db.session.add(AdminAccount(user_id=u.id, access_level="superadmin"))
        db.session.commit()
        if not os.environ.get("ALERTIFY_ADMIN_PASSWORD"):
            path = os.path.join(INSTANCE_DIR, "ADMIN_CREDENTIALS.txt")
            with open(path, "w") as fh:
                fh.write(f"ALERTIFY initial administrator\nEmail: {email}\nPassword: {pw}\n"
                         "Change this password after first login, then delete this file.\n")
            print(f"\n[ALERTIFY] Created administrator {email} — password saved to {path}\n", flush=True)


@app.cli.command("create-admin")
def create_admin_cmd():
    """flask --app app create-admin  — promote/create an admin interactively."""
    import getpass
    email = input("Admin email: ").strip().lower()
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(full_name=input("Full name: ").strip() or "Administrator", email=email)
        u.set_password(getpass.getpass("Password: "))
        db.session.add(u)
        db.session.flush()
    if not u.admin_account:
        db.session.add(AdminAccount(user_id=u.id))
    db.session.commit()
    print("Admin ready:", email)


with app.app_context():
    seed_database()

def port_in_use(host, port):
    """True if something is already listening on host:port."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", int(os.environ.get("PORT", 5000))
    # On Windows a second server can bind the same port without an error. Requests
    # then bounce between two copies (often from different folders, each with its
    # own database and secret key), so logins fail and form data is lost.
    # WERKZEUG_RUN_MAIN is set inside the debug reloader's child, which must start.
    if not os.environ.get("WERKZEUG_RUN_MAIN") and port_in_use(HOST, PORT):
        raise SystemExit(f"ALERTIFY is already running at http://{HOST}:{PORT}\n"
                         "Close the other ALERTIFY window/terminal first (Ctrl+C), then run this again.")
    print(f" * ALERTIFY folder:   {BASE_DIR}")
    from sqlalchemy.engine import make_url
    url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    print(f" * Database:          {url.database if url.drivername == 'sqlite' else url.render_as_string(hide_password=True)}")
    creds = os.path.join(INSTANCE_DIR, "ADMIN_CREDENTIALS.txt")
    if os.path.exists(creds):
        print(f" * Admin login file:  {creds}")
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host=HOST, port=PORT)
