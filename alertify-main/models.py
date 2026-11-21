"""ALERTIFY database models (SQLAlchemy).

Default engine is SQLite (instance/alertify.db). Set DATABASE_URL to use
MySQL (mysql+pymysql://...) or PostgreSQL (postgresql+psycopg://...).
"""
import json
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------- 1. Users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    barangay = db.Column(db.String(80))
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    reset_token = db.Column(db.String(64), index=True)
    reset_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    last_login = db.Column(db.DateTime)

    reports = db.relationship("DisasterReport", back_populates="user", lazy="dynamic")
    admin_account = db.relationship("AdminAccount", back_populates="user", uselist=False,
                                    foreign_keys="AdminAccount.user_id",
                                    cascade="all, delete-orphan")

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def is_active(self):  # Flask-Login: blocks deactivated accounts
        return self.is_active_account

    @property
    def is_admin(self):
        return self.admin_account is not None and self.admin_account.active

    @property
    def initials(self):
        parts = [p for p in self.full_name.split() if p]
        return "".join(p[0] for p in parts[:2]).upper() or "U"


# ---------------------------------------------------------- 8. Admin Accounts
class AdminAccount(db.Model):
    __tablename__ = "admin_accounts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    access_level = db.Column(db.String(20), default="superadmin")  # superadmin | editor
    active = db.Column(db.Boolean, default=True)
    granted_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    granted_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="admin_account")


# ------------------------------------------------------ 3. Disaster Categories
class DisasterCategory(db.Model):
    __tablename__ = "disaster_categories"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(60), nullable=False)
    icon = db.Column(db.String(10))
    description = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)


# --------------------------------------------------------- 4. Evacuation Centers
class EvacuationCenter(db.Model):
    __tablename__ = "evacuation_centers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))          # location text exactly as in source
    barangay = db.Column(db.String(80), index=True)
    capacity_families = db.Column(db.Integer)     # None = not provided in source
    capacity_persons = db.Column(db.Integer)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    source = db.Column(db.String(200))
    source_note = db.Column(db.String(255))
    # Verification: nothing is "official" until an administrator verifies it.
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Hazard suitability: comma separated category codes, admin-verified only.
    hazards = db.Column(db.String(200), default="")
    # Operational status: unknown unless an admin updates it.
    operational_status = db.Column(db.String(20), default="unknown")  # unknown|open|full|closed
    status_updated_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    @property
    def hazard_list(self):
        return [h for h in (self.hazards or "").split(",") if h]

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "location": self.location,
            "barangay": self.barangay,
            "capacity_families": self.capacity_families,
            "capacity_persons": self.capacity_persons,
            "lat": self.latitude, "lng": self.longitude,
            "source": self.source, "source_note": self.source_note,
            "verified": self.verified,
            "verified_at": self.verified_at.strftime("%b %d, %Y") if self.verified_at else None,
            "hazards": self.hazard_list,
            "operational_status": self.operational_status,
            "status_updated_at": self.status_updated_at.strftime("%b %d, %Y %I:%M %p")
            if self.status_updated_at else None,
        }


# --------------------------------------------------------- 5. Emergency Contacts
class EmergencyContact(db.Model):
    __tablename__ = "emergency_contacts"
    id = db.Column(db.Integer, primary_key=True)
    organization = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)
    numbers = db.Column(db.String(255), nullable=False)  # " / " separated
    description = db.Column(db.String(255))
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    sort_order = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)   # shown in quick-dial bar
    active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    @property
    def number_list(self):
        return [n.strip() for n in self.numbers.split("/") if n.strip()]

    def to_dict(self):
        return {"id": self.id, "organization": self.organization, "category": self.category,
                "numbers": self.number_list, "description": self.description,
                "verified": self.verified}


# ------------------------------------------------------- 6. Disaster Instructions
class DisasterInstruction(db.Model):
    """One instruction line.

    context = 'response' -> used by the assessment engine.  `section` is one of
              immediate|avoid|bring|evacuate|contact and `condition` is a flag
              key ('base', 'trapped', 'flood.rising', ...) produced by engine.py.
    context = 'guide'    -> Disaster Guide content. `section` is one of
              before|during|after|checklist|supplies|reminders|avoid.
    """
    __tablename__ = "disaster_instructions"
    id = db.Column(db.Integer, primary_key=True)
    disaster = db.Column(db.String(30), nullable=False, index=True)  # category code or 'general'
    context = db.Column(db.String(12), nullable=False, default="response")
    section = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(40), default="base")
    text = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, default=50)  # lower shows first
    source = db.Column(db.String(160))
    active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


# ------------------------------------------------------------ 2. Disaster Reports
class DisasterReport(db.Model):
    __tablename__ = "disaster_reports"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(16), unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    guest_token = db.Column(db.String(64), index=True)  # for reports made before login
    category_id = db.Column(db.Integer, db.ForeignKey("disaster_categories.id"), nullable=False)
    answers_json = db.Column(db.Text, default="{}")
    barangay = db.Column(db.String(80))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_accuracy = db.Column(db.Float)
    location_source = db.Column(db.String(20))  # gps | map_pin | manual
    people_count = db.Column(db.Integer, default=1)
    special_assistance = db.Column(db.String(255))
    description = db.Column(db.Text)
    severity = db.Column(db.String(12))       # low|moderate|high|critical
    severity_score = db.Column(db.Integer)
    flags = db.Column(db.String(255))
    instructions_json = db.Column(db.Text)    # snapshot of what ALERTIFY recommended
    recommended_center_id = db.Column(db.Integer, db.ForeignKey("evacuation_centers.id"))
    recommended_distance_km = db.Column(db.Float)
    status = db.Column(db.String(20), default="active")  # active|acknowledged|responding|resolved|closed
    saved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", back_populates="reports")
    category = db.relationship("DisasterCategory")
    recommended_center = db.relationship("EvacuationCenter")
    history = db.relationship("ReportHistory", back_populates="report",
                              order_by="ReportHistory.created_at",
                              cascade="all, delete-orphan")

    @property
    def answers(self):
        try:
            return json.loads(self.answers_json or "{}")
        except ValueError:
            return {}

    @property
    def instructions(self):
        try:
            return json.loads(self.instructions_json or "{}")
        except ValueError:
            return {}

    @property
    def flag_list(self):
        return [f for f in (self.flags or "").split(",") if f]


# --------------------------------------------------------------- 9. Report History
class ReportHistory(db.Model):
    """Audit trail of every event on a report (created, status changes, saved)."""
    __tablename__ = "report_history"
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("disaster_reports.id"), nullable=False, index=True)
    event = db.Column(db.String(30), nullable=False)  # created|status_change|saved|claimed|note
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    note = db.Column(db.String(500))
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=utcnow)

    report = db.relationship("DisasterReport", back_populates="history")
    actor = db.relationship("User")


# ---------------------------------------------------------------- 7. Notifications
class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    kind = db.Column(db.String(20), default="announcement")  # advisory|announcement|reminder|evacuation|instruction_change
    level = db.Column(db.String(12), default="info")         # info|advisory|warning|emergency
    source = db.Column(db.String(160))   # e.g. "CDRRMO Batangas City bulletin no. 3"
    barangay = db.Column(db.String(80))  # optional targeting; None = city-wide
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    expires_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)

    author = db.relationship("User")


class NotificationRead(db.Model):
    __tablename__ = "notification_reads"
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey("notifications.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    read_at = db.Column(db.DateTime, default=utcnow)
    __table_args__ = (db.UniqueConstraint("notification_id", "user_id"),)
