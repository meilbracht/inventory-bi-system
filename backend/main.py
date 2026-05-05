from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from db import Base, engine, get_db
from models import User, Item, Transaction
from auth import hash_password, verify_password, require_role
from fastapi import UploadFile, File
from datetime import datetime
from pydantic import BaseModel
import pandas as pd

Base.metadata.create_all(bind=engine)

app = FastAPI(title="USAF Inventory BI API")

class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # admin/clerk/viewer

class UserRoleUpdate(BaseModel):
    role: str

@app.get("/users")
def list_users(username: str, role: str, db: Session = Depends(get_db)):
    require_role(role, {"admin"})
    users = db.query(User).order_by(User.username).all()
    # Return safe fields only
    return [{"id": u.id, "username": u.username, "role": u.role, "is_active": getattr(u, "is_active", True)} for u in users]

@app.post("/users")
def create_user(username: str, role: str, body: UserCreate, db: Session = Depends(get_db)):
    require_role(role, {"admin"})
    if body.role not in {"admin", "clerk", "viewer"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    u = User(username=body.username, password_hash=hash_password(body.password), role=body.role)
    # if you added is_active
    if hasattr(u, "is_active"):
        u.is_active = True

    db.add(u); db.commit()
    return {"message": "User created"}

@app.put("/users/{user_id}/role")
def update_user_role(username: str, role: str, user_id: int, body: UserRoleUpdate, db: Session = Depends(get_db)):
    require_role(role, {"admin"})
    if body.role not in {"admin", "clerk", "viewer"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    u.role = body.role
    db.commit()
    return {"message": "Role updated"}

@app.delete("/users/{user_id}")
def delete_user(username: str, role: str, user_id: int, db: Session = Depends(get_db)):
    require_role(role, {"admin"})
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # Soft delete if is_active exists, else hard delete
    if hasattr(u, "is_active"):
        u.is_active = False
        db.commit()
        return {"message": "User disabled"}
    else:
        db.delete(u); db.commit()
        return {"message": "User deleted"}

# --- Seed an admin user once (you can remove later) ---
@app.post("/seed-admin")
def seed_admin(db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == "admin").first():
        return {"message": "Admin already exists"}
    u = User(username="admin", password_hash=hash_password("Admin123!"), role="admin")
    db.add(u); db.commit()
    return {"message": "Seeded admin: admin / Admin123!"}

# --- Login (simple for MVP) ---
@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == username).first()
    if not u or not verify_password(password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": u.username, "role": u.role}

# --- Search items (all roles can view) ---
@app.get("/items")
def search_items(q: str = "", base: str = "", db: Session = Depends(get_db)):
    query = db.query(Item)
    if base:
        query = query.filter(Item.base_location == base)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Item.stock_number.like(like)) |
            (Item.noun.like(like)) |
            (Item.bin_location.like(like)) |
            (Item.keywords.like(like))
        )
    return query.order_by(Item.stock_number).limit(500).all()

@app.get("/transactions")
def get_transactions(
    base: str = "",
    stock_number: str = "",
    limit: int = 500,
    db: Session = Depends(get_db)
):
    q = db.query(Transaction)

    if base:
        q = q.filter(Transaction.base_location == base)

    if stock_number:
        q = q.filter(Transaction.stock_number == stock_number)

    # newest first
    rows = q.order_by(Transaction.created_at.desc()).limit(limit).all()
    return rows

# --- Create/Update item (Admin only) ---
@app.post("/items")
def create_item(username: str, role: str, item: dict, db: Session = Depends(get_db)):
    require_role(role, {"admin"})
    it = Item(**item)
    db.add(it); db.commit()
    return {"message": "Created"}

# --- Adjust quantity (Admin + Clerk) ---
@app.post("/items/adjust")
def adjust_qty(
    username: str,
    role: str,
    stock_number: str,
    base_location: str,
    action: str,
    qty: int,
    reason: str,
    db: Session = Depends(get_db),
):
    require_role(role, {"admin", "clerk"})

    it = db.query(Item).filter(
        Item.stock_number == stock_number,
        Item.base_location == base_location
    ).first()

    if not it:
        raise HTTPException(status_code=404, detail="Item not found")

    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be > 0")

    before = it.actual_qty

    if action == "add":
        it.actual_qty += qty
    elif action == "subtract":
        it.actual_qty -= qty
        if it.actual_qty < 0:
            raise HTTPException(status_code=400, detail="Cannot go below 0")
    else:
        raise HTTPException(status_code=400, detail="action must be add or subtract")

    after = it.actual_qty

    t = Transaction(
        stock_number=stock_number,
        base_location=base_location,
        username=username,
        action=action,
        qty_change=qty,
        qty_before=before,
        qty_after=after,
        reason=reason,
    )
    db.add(t)
    db.commit()

    return {"message": "Adjusted", "before": before, "after": after}


@app.post("/import-excel")
def import_excel(username: str, role: str, base_location: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    require_role(role, {"admin"})

    # Read Excel
    df = pd.read_excel(file.file)

    # Normalize column names (makes import tolerant)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Expected columns (lowercase)
    required = {
        "stock number",
        "noun",
        "bin location",
        "unit of issue",
        "actual qty",
        "authorized qty",
        "unit price",
        "keywords",
    }
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {sorted(list(missing))}")

    inserted = 0
    updated = 0

    for _, row in df.iterrows():
        stock = str(row["stock number"]).strip()
        noun = str(row["noun"]).strip()
        bin_loc = str(row["bin location"]).strip()
        uoi = str(row["unit of issue"]).strip()
        keywords = "" if pd.isna(row["keywords"]) else str(row["keywords"]).strip()

        actual_qty = int(row["actual qty"]) if not pd.isna(row["actual qty"]) else 0
        auth_qty = int(row["authorized qty"]) if not pd.isna(row["authorized qty"]) else 0
        unit_price = float(row["unit price"]) if not pd.isna(row["unit price"]) else 0.0

        existing = db.query(Item).filter(
            Item.stock_number == stock,
            Item.base_location == base_location
        ).first()

        if existing:
            existing.noun = noun
            existing.bin_location = bin_loc
            existing.unit_of_issue = uoi
            existing.actual_qty = actual_qty
            existing.authorized_qty = auth_qty
            existing.unit_price = unit_price
            existing.keywords = keywords
            updated += 1
        else:
            it = Item(
                stock_number=stock,
                noun=noun,
                bin_location=bin_loc,
                unit_of_issue=uoi,
                actual_qty=actual_qty,
                authorized_qty=auth_qty,
                unit_price=unit_price,
                keywords=keywords,
                base_location=base_location
            )
            db.add(it)
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

@app.post("/import/items")
def import_items(
    username: str,
    role: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    require_role(role, {"admin"})

    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    df = pd.read_excel(file.file)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    required = {
        "stock number": "stock_number",
        "noun": "noun",
        "bin location": "bin_location",
        "unit of issue": "unit_of_issue",
        "actual qty": "actual_qty",
        "authorized qty": "authorized_qty",
        "unit price": "unit_price",
        "keywords": "keywords",
        "base": "base_location",
    }

    missing = [k for k in required if k not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {missing}"
        )

    count = 0
    for _, row in df.iterrows():
        item = Item(
            stock_number=str(row["stock number"]).strip(),
            noun=str(row["noun"]).strip(),
            bin_location=str(row["bin location"]).strip(),
            unit_of_issue=str(row["unit of issue"]).strip(),
            actual_qty=int(row["actual qty"]),
            authorized_qty=int(row["authorized qty"]),
            unit_price=float(row["unit price"]),
            keywords=str(row.get("keywords", "")).strip(),
            base_location=str(row["base"]).strip(),
        )
        db.add(item)
        count += 1

    db.commit()
    return {"imported": count}

