from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "admin", "clerk", "viewer"
    is_active = Column(Boolean, default=True)


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)

    stock_number = Column(String, index=True, nullable=False)      # Excel: stock number
    noun = Column(String, nullable=False)                          # Excel: noun/nomenclature
    bin_location = Column(String, nullable=False)                  # Excel: bin location
    unit_of_issue = Column(String, nullable=False)                 # Excel: unit of issue

    actual_qty = Column(Integer, nullable=False, default=0)         # Excel: actual qty
    authorized_qty = Column(Integer, nullable=False, default=0)     # Excel: authorized qty
    unit_price = Column(Float, nullable=False, default=0.0)         # Excel: unit price

    keywords = Column(String, nullable=True)                        # Excel: keywords
    base_location = Column(String, index=True, nullable=False)      # for multi-location


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    stock_number = Column(String, nullable=False)
    base_location = Column(String, nullable=False)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)  # add/subtract/edit
    qty_change = Column(Integer, nullable=False)
    qty_before = Column(Integer, nullable=False)
    qty_after = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
