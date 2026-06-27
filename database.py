"""
database.py
All MongoDB operations for BMS Cloud.
"""

import os
import bcrypt
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv

load_dotenv()

_client = None
_db     = None

def get_db():
    global _client, _db
    if _db is None:
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri)
        _db = _client[os.environ.get("DB_NAME", "bms")]
    return _db


def init_db():
    """Create indexes and seed default users."""
    db = get_db()

    db.users.create_index("username", unique=True)
    db.tickets.create_index("upload_id", unique=True, sparse=True)
    db.tickets.create_index([("date", DESCENDING)])
    db.master.create_index([("type", 1), ("name", 1)], unique=True)

    # Seed admin
    if db.users.count_documents({"role": "admin"}) == 0:
        db.users.insert_one({
            "username":      "admin",
            "password_hash": bcrypt.hashpw(b"admin123", bcrypt.gensalt()),
            "role":          "admin",
            "created_at":    datetime.utcnow()
        })
    # Seed BD incharge
    if db.users.count_documents({"role": "bd_incharge"}) == 0:
        db.users.insert_one({
            "username":      "bdincharge",
            "password_hash": bcrypt.hashpw(b"bd123", bcrypt.gensalt()),
            "role":          "bd_incharge",
            "created_at":    datetime.utcnow()
        })


# ── AUTH ──────────────────────────────────────────────────────
def authenticate_user(username, password):
    db   = get_db()
    user = db.users.find_one({"username": username})
    if not user:
        return None
    pw = password.encode() if isinstance(password, str) else password
    if bcrypt.checkpw(pw, user["password_hash"]):
        return user
    return None


def get_all_users():
    db = get_db()
    return list(db.users.find({}, {"password_hash": 0}).sort("username", 1))


def add_user(username, password, role):
    db = get_db()
    db.users.insert_one({
        "username":      username,
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
        "role":          role,
        "created_at":    datetime.utcnow()
    })


def delete_user(user_id):
    db = get_db()
    db.users.delete_one({"_id": ObjectId(user_id)})


def change_password(user_id, new_password):
    db = get_db()
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())}}
    )


# ── MASTER DATA ───────────────────────────────────────────────
def get_master(mtype):
    db = get_db()
    docs = db.master.find({"type": mtype, "active": True}, {"name": 1}).sort("name", 1)
    return [d["name"] for d in docs]


def get_all_master(mtype):
    db = get_db()
    docs = db.master.find({"type": mtype}).sort("name", 1)
    return [{"id": str(d["_id"]), "name": d["name"], "active": d.get("active", True)} for d in docs]


def add_master(mtype, name):
    db = get_db()
    db.master.update_one(
        {"type": mtype, "name": name},
        {"$setOnInsert": {"type": mtype, "name": name, "active": True}},
        upsert=True
    )


def toggle_master(item_id, active):
    db = get_db()
    db.master.update_one({"_id": ObjectId(item_id)}, {"$set": {"active": active}})


def delete_master(item_id):
    db = get_db()
    db.master.delete_one({"_id": ObjectId(item_id)})


def get_vehicles():     return get_master("vehicle")
def get_technicians():  return get_master("technician")
def get_electricians(): return get_master("electrician")
def get_drivers():      return get_master("driver")


# ── TICKETS ───────────────────────────────────────────────────
def _clean(ticket):
    """Convert ObjectId to str for JSON serialisation."""
    if ticket:
        ticket["id"] = str(ticket.pop("_id"))
    return ticket


def add_ticket(data):
    db  = get_db()
    doc = {
        "upload_id":                data.get("upload_id"),
        "date":                     data.get("date"),
        "token_no":                 data.get("token_no"),
        "rc_no":                    data.get("rc_no"),
        "assigned_time":            data.get("assigned_time"),
        "reach_time":               data.get("reach_time"),
        "resolution_time":          data.get("resolution_time"),
        "vehicle_used":             data.get("vehicle_used"),
        "technician":               data.get("technician"),
        "electrician":              data.get("electrician"),
        "driver":                   data.get("driver"),
        "reach_delay_reason":       data.get("reach_delay_reason"),
        "resolution_delay_reason":  data.get("resolution_delay_reason"),
        "status":                   data.get("status"),
        "submitted_by":             data.get("submitted_by"),
        "created_at":               datetime.utcnow()
    }
    result = db.tickets.insert_one(doc)
    return str(result.inserted_id)


def upload_ticket_safe(data):
    db        = get_db()
    upload_id = data.get("upload_id")
    if upload_id:
        existing = db.tickets.find_one({"upload_id": upload_id})
        if existing:
            return "duplicate", str(existing["_id"])
    ticket_id = add_ticket(data)
    return "inserted", ticket_id


def get_all_tickets(limit=500):
    db   = get_db()
    docs = db.tickets.find().sort("created_at", DESCENDING).limit(limit)
    return [_clean(d) for d in docs]


def get_ticket_by_id(ticket_id):
    db  = get_db()
    doc = db.tickets.find_one({"_id": ObjectId(ticket_id)})
    return _clean(doc)


def search_tickets(token_no="", rc_no="", technician="",
                   from_date=None, to_date=None):
    db    = get_db()
    query = {}
    if token_no:   query["token_no"]   = {"$regex": token_no,   "$options": "i"}
    if rc_no:      query["rc_no"]      = {"$regex": rc_no,      "$options": "i"}
    if technician: query["technician"] = {"$regex": technician, "$options": "i"}
    if from_date or to_date:
        query["date"] = {}
        if from_date: query["date"]["$gte"] = from_date
        if to_date:   query["date"]["$lte"] = to_date
    docs = db.tickets.find(query).sort("created_at", DESCENDING).limit(500)
    return [_clean(d) for d in docs]


def update_ticket(ticket_id, data):
    db = get_db()
    db.tickets.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$set": {
            "date":                    data.get("date"),
            "token_no":                data.get("token_no"),
            "rc_no":                   data.get("rc_no"),
            "assigned_time":           data.get("assigned_time"),
            "reach_time":              data.get("reach_time"),
            "resolution_time":         data.get("resolution_time"),
            "vehicle_used":            data.get("vehicle_used"),
            "technician":              data.get("technician"),
            "electrician":             data.get("electrician"),
            "driver":                  data.get("driver"),
            "reach_delay_reason":      data.get("reach_delay_reason"),
            "resolution_delay_reason": data.get("resolution_delay_reason"),
            "status":                  data.get("status"),
            "updated_at":              datetime.utcnow()
        }}
    )


def delete_ticket(ticket_id):
    db = get_db()
    db.tickets.delete_one({"_id": ObjectId(ticket_id)})


# ── ANALYTICS ─────────────────────────────────────────────────
def get_tickets_in_range(from_date, to_date):
    db   = get_db()
    docs = db.tickets.find({"date": {"$gte": from_date, "$lte": to_date}})
    return [_clean(d) for d in docs]


def get_summary_counts(from_date, to_date):
    rows  = get_tickets_in_range(from_date, to_date)
    total = len(rows)
    conf  = sum(1 for r in rows if (r.get("status") or "").upper() == "CONF")
    nc    = total - conf
    return {
        "total":    total,
        "conf":     conf,
        "nc":       nc,
        "conf_pct": round(conf / total * 100, 1) if total else 0,
        "nc_pct":   round(nc   / total * 100, 1) if total else 0,
    }


def get_technician_performance(from_date, to_date):
    rows  = get_tickets_in_range(from_date, to_date)
    stats = {}
    for r in rows:
        tech = (r.get("technician") or "Unassigned").strip() or "Unassigned"
        if tech not in stats:
            stats[tech] = {"technician": tech, "total": 0, "conf": 0, "nc": 0}
        stats[tech]["total"] += 1
        if (r.get("status") or "").upper() == "CONF":
            stats[tech]["conf"] += 1
        else:
            stats[tech]["nc"] += 1
    result = list(stats.values())
    for s in result:
        s["conf_pct"] = round(s["conf"] / s["total"] * 100, 1) if s["total"] else 0
    result.sort(key=lambda x: x["total"], reverse=True)
    return result
