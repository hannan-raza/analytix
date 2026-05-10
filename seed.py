"""
Seed script — drops and recreates all tables, then inserts realistic test data.

Generates:
    - 100 users (registered across the last ~6 months)
    - 50 products (mixed retail: electronics, apparel, home)
    - ~300 orders (weighted toward recent dates, with realistic buying patterns)

Run from the project root with the venv active:
    python seed.py
"""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

from app.db.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order

# Deterministic — same seed = same data every run. Useful for demos.
rng = random.Random(42)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
PW = pwd.hash("password123")

# Anchor "today" to the date the script is run, so time-relative queries
# ("last 7 days", "this month") always work in the demo.
NOW = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)


# ── DATA POOLS ─────────────────────────────────────────────────────────────
FIRST_NAMES = [
    # ── English / Western ─────────────────────────────────────────
    "James", "Emma", "Oliver", "Sophia", "William", "Charlotte", "Benjamin", "Amelia",
    "Lucas", "Mia", "Henry", "Isabella", "Alexander", "Ava", "Ethan", "Harper",
    "Daniel", "Evelyn", "Matthew", "Abigail", "Jack", "Emily", "Samuel", "Elizabeth",
    "David", "Sofia", "Joseph", "Avery", "Carter", "Ella", "Owen", "Scarlett",
    "Wyatt", "Grace", "John", "Chloe", "Luke", "Victoria", "Jayden", "Riley",
    "Michael", "Aria", "Ryan", "Lily", "Andrew", "Hannah", "Thomas", "Zoe",

    # ── European ──────────────────────────────────────────────────
    "Lukas", "Leonie", "Felix", "Marie", "Maximilian", "Lena", "Jonas", "Mila",
    "Mateo", "Lucia", "Hugo", "Martina", "Pierre", "Camille", "Antoine", "Manon",

    # ── South Asian ───────────────────────────────────────────────
    "Ali", "Sara", "Ahmed", "Fatima", "Zara", "Bilal", "Aisha", "Omar",
    "Priya", "Arjun", "Ananya", "Rohan", "Diya", "Vikram", "Neha", "Hassan",

    # ── East Asian ────────────────────────────────────────────────
    "Wei", "Mei", "Hiroshi", "Yuki", "Min-jun", "Seo-yeon", "Akira", "Sakura",

    # ── Middle Eastern ────────────────────────────────────────────
    "Yousef", "Layla", "Karim", "Nour", "Tariq", "Amira",

    # ── Latin American ────────────────────────────────────────────
    "Diego", "Valentina", "Mateus", "Isabela", "Carlos", "Camila",

    # ── African ───────────────────────────────────────────────────
    "Kwame", "Amara", "Tunde", "Zola", "Sipho", "Thandi",
]

LAST_NAMES = [
    # ── English / Western ─────────────────────────────────────────
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson",
    "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Walker",
    "Hall", "Allen", "Young", "King", "Wright", "Scott", "Green", "Baker",
    "Adams", "Nelson", "Carter", "Mitchell", "Roberts", "Turner", "Phillips", "Campbell",
    "Parker", "Evans", "Edwards", "Collins", "Stewart", "Morris", "Murphy", "Cook",

    # ── European ──────────────────────────────────────────────────
    "Muller", "Schmidt", "Fischer", "Weber", "Wagner", "Becker",
    "Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Hernandez",
    "Rossi", "Bianchi", "Romano", "Ferrari",
    "Dubois", "Laurent", "Moreau", "Bernard",

    # ── South Asian ───────────────────────────────────────────────
    "Khan", "Ahmed", "Hussain", "Malik", "Sheikh", "Raza",
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy",

    # ── East Asian ────────────────────────────────────────────────
    "Chen", "Wang", "Li", "Zhang", "Tanaka", "Nakamura", "Kim", "Park",

    # ── Middle Eastern ────────────────────────────────────────────
    "Mansour", "Saleh", "Khoury", "Haddad",

    # ── Latin American ────────────────────────────────────────────
    "Silva", "Santos", "Costa", "Oliveira",

    # ── African ───────────────────────────────────────────────────
    "Okonkwo", "Mensah", "Diallo", "Nkosi",
]

# Mixed retail product catalog: electronics, apparel, home
PRODUCT_CATALOG = [
    # ── ELECTRONICS ─────────────────────────────────────────────
    ("MacBook Pro 14\"",          1999.00, 35),
    ("MacBook Air M3",            1199.00, 60),
    ("Dell XPS 13",               1299.00, 45),
    ("HP Pavilion Laptop",         749.00, 80),
    ("iPhone 15 Pro",             1099.00, 70),
    ("iPhone 15",                  799.00, 95),
    ("Samsung Galaxy S24 Ultra",  1199.00, 55),
    ("Google Pixel 8",             699.00, 65),
    ("iPad Air",                   599.00, 75),
    ("iPad Pro 11\"",              899.00, 40),
    ("Samsung Galaxy Tab S9",      649.00, 50),
    ("AirPods Pro (2nd Gen)",      249.00, 200),
    ("Sony WH-1000XM5 Headphones", 399.00, 90),
    ("Bose QuietComfort 45",       329.00, 70),
    ("Apple Watch Series 9",       399.00, 110),
    ("Samsung Galaxy Watch 6",     299.00, 85),
    ("LG 27\" 4K Monitor",         449.00, 60),
    ("Dell UltraSharp 27\"",       529.00, 45),
    ("Logitech MX Master 3S Mouse", 99.00, 250),
    ("Keychron K8 Keyboard",       129.00, 180),

    # ── APPAREL ─────────────────────────────────────────────────
    ("Nike Air Max 270",           150.00, 120),
    ("Adidas Ultraboost 22",       180.00, 95),
    ("Levi's 501 Original Jeans",   89.00, 220),
    ("Uniqlo Heattech Crew Neck",   19.99, 400),
    ("Zara Wool Blend Coat",       149.00, 70),
    ("H&M Cotton T-Shirt",          12.99, 500),
    ("Tommy Hilfiger Polo Shirt",   59.00, 180),
    ("Calvin Klein Cotton Boxers",  29.99, 350),
    ("Ray-Ban Aviator Sunglasses", 169.00, 90),
    ("Casio G-Shock Watch",        119.00, 130),
    ("Nike Dri-FIT Training Shorts", 35.00, 280),
    ("Adidas Originals Hoodie",     75.00, 160),
    ("North Face Puffer Jacket",   249.00, 55),
    ("Puma Running Sneakers",       95.00, 140),
    ("Tommy Hilfiger Crossbody Bag", 89.00, 100),

    # ── HOME ────────────────────────────────────────────────────
    ("IKEA Malm Bed Frame Queen",  299.00, 40),
    ("Dyson V15 Cordless Vacuum",  749.00, 35),
    ("Philips Air Fryer XXL",      229.00, 75),
    ("Nespresso Vertuo Plus",      199.00, 90),
    ("Instant Pot Duo 7-in-1",     119.00, 120),
    ("KitchenAid Stand Mixer",     449.00, 50),
    ("Le Creuset Dutch Oven",      379.00, 45),
    ("Brooklinen Luxe Sheet Set",  179.00, 110),
    ("Casper Original Pillow",      75.00, 200),
    ("Dyson Pure Cool Air Purifier", 549.00, 40),
    ("Roomba i7+ Robot Vacuum",    799.00, 30),
    ("Vitamix 5200 Blender",       549.00, 55),
    ("Breville Espresso Machine",  699.00, 45),
    ("West Elm Mid-Century Lamp",  199.00, 80),
    ("Crate & Barrel Throw Blanket", 89.00, 150),
]


def ts(year, month, day, hour=None, minute=None):
    """Build a timezone-aware UTC datetime."""
    return datetime(
        year, month, day,
        hour if hour is not None else rng.randint(8, 22),
        minute if minute is not None else rng.randint(0, 59),
        rng.randint(0, 59),
        tzinfo=timezone.utc,
    )


def date_offset(days_ago, hour=None):
    """Return a datetime `days_ago` days before NOW, with random time of day."""
    base = NOW - timedelta(days=days_ago)
    return base.replace(
        hour=hour if hour is not None else rng.randint(8, 22),
        minute=rng.randint(0, 59),
        second=rng.randint(0, 59),
        microsecond=0,
    )


def generate_users():
    """100 users, registered across the last ~180 days, with growth bias toward recent."""
    users = []
    used_emails = set()
    used_names = set()

    # Skew registrations toward recent dates (more growth lately)
    # Bucket: 40 users in last 60 days, 35 in 60-120 days ago, 25 in 120-180 days ago
    buckets = (
        [(0, 60)] * 40
        + [(60, 120)] * 35
        + [(120, 180)] * 25
    )
    rng.shuffle(buckets)

    for i, (lo, hi) in enumerate(buckets):
        # Build a unique name
        for _ in range(50):
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            full = f"{first} {last}"
            if full not in used_names:
                used_names.add(full)
                break
        else:
            full = f"{first} {last} {i}"  # extreme fallback

        # Build a unique email
        base_email = f"{first.lower()}.{last.lower()}"
        email = f"{base_email}@example.com"
        suffix = 1
        while email in used_emails:
            suffix += 1
            email = f"{base_email}{suffix}@example.com"
        used_emails.add(email)

        days_ago = rng.randint(lo, hi - 1)
        users.append(User(
            name=full,
            email=email,
            password=PW,
            created_at=date_offset(days_ago),
        ))

    # Guarantee a few specific recency markers for demo queries
    users[-1].created_at = date_offset(0, hour=10)   # registered today
    users[-2].created_at = date_offset(1, hour=15)   # yesterday
    users[-3].created_at = date_offset(3, hour=11)   # 3 days ago
    users[-4].created_at = date_offset(6, hour=14)   # within last 7 days

    return users


def generate_products():
    """50 products from the mixed-retail catalog, with stagger creation dates."""
    catalog = list(PRODUCT_CATALOG)
    rng.shuffle(catalog)
    chosen = catalog[:50]

    products = []
    # Spread product creation across the last ~200 days (catalog grows over time)
    for i, (name, price, stock) in enumerate(chosen):
        # Older products earlier in the list, newer toward the end
        days_ago = rng.randint(0, 200)
        products.append(Product(
            name=name,
            price=price,
            stock=stock,
            created_at=date_offset(days_ago),
        ))

    # Guarantee some recent product additions for demo queries
    products[-1].created_at = date_offset(0, hour=9)    # added today
    products[-2].created_at = date_offset(2, hour=16)   # last 7 days
    products[-3].created_at = date_offset(5, hour=13)   # last 7 days

    return products


def generate_orders(users, products):
    """
    ~300 orders with realistic patterns:
      - More recent orders than old (growing business).
      - Most users buy 1-4 times, a handful buy 8-15 times (power users).
      - ~10 users never buy (in-flight signups).
      - Most orders are 1-2 units; occasional bulk 3-6.
    """
    orders = []

    # Pick ~10% of users as never-buyers
    eligible_users = users[:]
    rng.shuffle(eligible_users)
    never_buyers = set(u.email for u in eligible_users[:10])
    buyers = [u for u in users if u.email not in never_buyers]

    # Assign a "purchase profile" to each buyer
    profiles = []
    for u in buyers:
        roll = rng.random()
        if roll < 0.08:
            count = rng.randint(8, 15)   # power user (~8% of buyers)
        elif roll < 0.40:
            count = rng.randint(3, 6)    # regular (~32%)
        else:
            count = rng.randint(1, 3)    # occasional (~60%)
        profiles.append((u, count))

    # Generate orders per user
    for user, order_count in profiles:
        # User can only buy after they registered
        user_age_days = (NOW - user.created_at).days
        if user_age_days < 1:
            continue  # registered today, no orders yet

        for _ in range(order_count):
            # Order date: somewhere between registration and now,
            # weighted slightly toward more recent.
            max_days_back = min(user_age_days, 180)
            # Bias toward recent: square the random to push values toward 0
            r = rng.random() ** 2
            days_ago = int(r * max_days_back)

            product = rng.choice(products)
            # Quantity: 70% buy 1, 20% buy 2, 8% buy 3-4, 2% bulk 5-8
            q_roll = rng.random()
            if q_roll < 0.70:
                qty = 1
            elif q_roll < 0.90:
                qty = 2
            elif q_roll < 0.98:
                qty = rng.randint(3, 4)
            else:
                qty = rng.randint(5, 8)

            orders.append(Order(
                user_id=user.id,
                product_id=product.id,
                quantity=qty,
                total_price=round(product.price * qty, 2),
                created_at=date_offset(days_ago),
            ))

    # Trim/pad to roughly 300
    rng.shuffle(orders)
    orders = orders[:300]

    # Guarantee recency markers for time-filter demo queries
    if len(orders) >= 10:
        orders[0].created_at = date_offset(0, hour=14)   # today
        orders[1].created_at = date_offset(0, hour=18)   # today
        orders[2].created_at = date_offset(2, hour=11)   # last 7 days
        orders[3].created_at = date_offset(4, hour=16)   # last 7 days
        orders[4].created_at = date_offset(6, hour=20)   # last 7 days

    return orders


def run():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Generating users...")
        users = generate_users()
        db.add_all(users)
        db.flush()

        print("Generating products...")
        products = generate_products()
        db.add_all(products)
        db.flush()

        print("Generating orders...")
        orders = generate_orders(users, products)
        db.add_all(orders)
        db.commit()

        # ── SUMMARY ──────────────────────────────────────────────────────
        today = sum(1 for o in orders if (NOW - o.created_at).days == 0)
        last_7 = sum(1 for o in orders if (NOW - o.created_at).days <= 7)
        last_30 = sum(1 for o in orders if (NOW - o.created_at).days <= 30)
        revenue = sum(float(o.total_price) for o in orders)

        print("\nSeed complete.")
        print(f"  Users:    {len(users)}")
        print(f"  Products: {len(products)}")
        print(f"  Orders:   {len(orders)}")
        print(f"  Revenue:  ${revenue:,.2f}")
        print("\nTime filter coverage (orders):")
        print(f"  today        : {today}")
        print(f"  last 7 days  : {last_7}")
        print(f"  last 30 days : {last_30}")
        print(f"  older        : {len(orders) - last_30}")

    except Exception as e:
        db.rollback()
        print(f"\nSeed FAILED: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()