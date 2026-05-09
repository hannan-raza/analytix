"""
Seed script — drops and recreates all tables, then inserts test data.

Run from the project root with the venv active:
    python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

from app.db.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
PW = pwd.hash("password123")


def ts(year, month, day, hour=9):
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


def run():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── USERS ─────────────────────────────────────────────────────────
        # Spread across last ~60 days; last 2 registered in the last 7 days,
        # 1 registered today (2026-05-07).
        user_rows = [
            User(name="Ali Hassan",   email="ali@example.com",    password=PW, created_at=ts(2026, 3, 10)),
            User(name="Sara Khan",    email="sara@example.com",   password=PW, created_at=ts(2026, 3, 22)),
            User(name="Ahmed Raza",   email="ahmed@example.com",  password=PW, created_at=ts(2026, 4,  1)),
            User(name="Fatima Malik", email="fatima@example.com", password=PW, created_at=ts(2026, 4,  9)),
            User(name="Usman Ali",    email="usman@example.com",  password=PW, created_at=ts(2026, 4, 15)),
            User(name="Zara Ahmed",   email="zara@example.com",   password=PW, created_at=ts(2026, 4, 20)),
            User(name="Bilal Sheikh", email="bilal@example.com",  password=PW, created_at=ts(2026, 4, 27)),
            User(name="Aisha Noor",   email="aisha@example.com",  password=PW, created_at=ts(2026, 5,  1)),  # last 7 days
            User(name="Omar Farooq",  email="omar@example.com",   password=PW, created_at=ts(2026, 5,  5)),  # last 7 days
            User(name="Hina Javed",   email="hina@example.com",   password=PW, created_at=ts(2026, 5,  7)),  # today
        ]
        db.add_all(user_rows)
        db.flush()

        # ── PRODUCTS ──────────────────────────────────────────────────────
        # Mix of categories, 1 added today and 2 in the last 7 days.
        product_rows = [
            Product(name="Laptop Pro 15",      price=1299.99, stock=42,  created_at=ts(2026, 3,  8)),
            Product(name="iPhone 15",          price= 999.99, stock=85,  created_at=ts(2026, 3, 18)),
            Product(name="Sony Headphones",    price= 249.99, stock=130, created_at=ts(2026, 3, 26)),
            Product(name="Mechanical Keyboard",price=  89.99, stock=200, created_at=ts(2026, 4,  3)),
            Product(name='Dell Monitor 27"',   price= 399.99, stock=60,  created_at=ts(2026, 4, 10)),
            Product(name="Wireless Mouse",     price=  49.99, stock=300, created_at=ts(2026, 4, 17)),
            Product(name="USB-C Hub",          price=  34.99, stock=250, created_at=ts(2026, 4, 24)),
            Product(name="iPad Air",           price= 749.99, stock=55,  created_at=ts(2026, 5,  2)),  # last 7 days
            Product(name="Samsung Galaxy S24", price= 899.99, stock=70,  created_at=ts(2026, 5,  4)),  # last 7 days
            Product(name="AirPods Pro",        price= 249.99, stock=110, created_at=ts(2026, 5,  7)),  # today
        ]
        db.add_all(product_rows)
        db.flush()

        u = user_rows      # shorthand
        p = product_rows

        # ── ORDERS ────────────────────────────────────────────────────────
        # 15 orders — 1 today, 5 in last 7 days, 9 in last 30 days, 5 older.
        order_rows = [
            # Older than 30 days
            Order(user_id=u[0].id, product_id=p[0].id, quantity=1, total_price=1299.99, created_at=ts(2026, 3, 20)),
            Order(user_id=u[1].id, product_id=p[1].id, quantity=1, total_price= 999.99, created_at=ts(2026, 3, 28)),
            Order(user_id=u[2].id, product_id=p[2].id, quantity=2, total_price= 499.98, created_at=ts(2026, 4,  4)),
            Order(user_id=u[0].id, product_id=p[3].id, quantity=1, total_price=  89.99, created_at=ts(2026, 4,  6)),
            # Last 30 days (but older than 7 days)
            Order(user_id=u[3].id, product_id=p[4].id, quantity=1, total_price= 399.99, created_at=ts(2026, 4, 12)),
            Order(user_id=u[1].id, product_id=p[5].id, quantity=3, total_price= 149.97, created_at=ts(2026, 4, 17)),
            Order(user_id=u[4].id, product_id=p[6].id, quantity=2, total_price=  69.98, created_at=ts(2026, 4, 21)),
            Order(user_id=u[5].id, product_id=p[0].id, quantity=1, total_price=1299.99, created_at=ts(2026, 4, 24)),
            Order(user_id=u[2].id, product_id=p[7].id, quantity=1, total_price= 749.99, created_at=ts(2026, 4, 28)),
            # Last 7 days
            Order(user_id=u[6].id, product_id=p[1].id, quantity=1, total_price= 999.99, created_at=ts(2026, 5,  1)),
            Order(user_id=u[3].id, product_id=p[8].id, quantity=1, total_price= 899.99, created_at=ts(2026, 5,  2)),
            Order(user_id=u[7].id, product_id=p[2].id, quantity=1, total_price= 249.99, created_at=ts(2026, 5,  3)),
            Order(user_id=u[4].id, product_id=p[9].id, quantity=2, total_price= 499.98, created_at=ts(2026, 5,  5)),
            Order(user_id=u[8].id, product_id=p[3].id, quantity=2, total_price= 179.98, created_at=ts(2026, 5,  6)),
            # Today (2026-05-07)
            Order(user_id=u[9].id, product_id=p[5].id, quantity=1, total_price=  49.99, created_at=ts(2026, 5,  7)),
        ]
        db.add_all(order_rows)
        db.commit()

        print("\nSeed complete.")
        print(f"  Users:    {len(user_rows)}")
        print(f"  Products: {len(product_rows)}")
        print(f"  Orders:   {len(order_rows)}")
        print("\nTime filter coverage (orders):")
        print("  today        : 1  order  (2026-05-07)")
        print("  last 7 days  : 6  orders (2026-05-01 – 2026-05-07)")
        print("  last 30 days : 11 orders (2026-04-07 – 2026-05-07)")

    except Exception as e:
        db.rollback()
        print(f"\nSeed FAILED: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
