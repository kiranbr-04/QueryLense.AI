import os
import json
from datetime import datetime, timezone
from app.database.session import init_db, SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.connection import DatabaseConnection
from app.models.schema_metadata import SchemaMetadata
from app.core.security import get_password_hash
from app.database.connection_manager import get_engine_for_connection
from app.database.schema_inspector import discover_database_schema

SAMPLE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample-databases", "ecommerce_sample.db"))

def seed_demo_data():
    init_db()
    db = SessionLocal()

    try:
        # Check if demo organization already exists
        existing_org = db.query(Organization).filter(Organization.slug == "acme-global").first()
        if existing_org:
            print("Demo data already seeded.")
            return

        # 1. Create Organization
        org = Organization(
            name="Acme Global Enterprises",
            slug="acme-global",
            plan="enterprise",
        )
        db.add(org)
        db.flush()

        # 2. Create Admin User
        admin = User(
            organization_id=org.id,
            email="admin@querylens.ai",
            hashed_password=get_password_hash("Admin123!"),
            full_name="Chief Data Officer",
            role="admin",
            is_active=True,
        )
        db.add(admin)

        # 3. Create Sample Database Connection
        conn = DatabaseConnection(
            organization_id=org.id,
            name="E-Commerce & Operations DB",
            connection_type="direct",
            dialect="sqlite",
            database_name=SAMPLE_DB_PATH,
            status="connected",
            last_tested_at=datetime.now(timezone.utc),
        )
        db.add(conn)
        db.flush()

        # 4. Discover & Save Schema
        engine = get_engine_for_connection(conn)
        tables = discover_database_schema(engine, conn.id)
        for t in tables:
            meta = SchemaMetadata(
                connection_id=conn.id,
                schema_name=t.get("schema_name", "public"),
                table_name=t["table_name"],
                table_type=t.get("table_type", "table"),
                columns_json=t["columns_json"],
                primary_keys_json=t.get("primary_keys_json", "[]"),
                foreign_keys_json=t.get("foreign_keys_json", "[]"),
                indexes_json=t.get("indexes_json", "[]"),
                row_count_estimate=t.get("row_count_estimate"),
                business_description=(
                    "Core employee records including compensation and departments" if t["table_name"] == "employees"
                    else "E-commerce customer orders with transaction totals" if t["table_name"] == "orders"
                    else "Company products, catalog pricing, and inventory quantities" if t["table_name"] == "products"
                    else ""
                ),
            )
            db.add(meta)

        conn.schema_discovered_at = datetime.now(timezone.utc)
        db.commit()
        print("Demo workspace pre-seeded successfully:")
        print("  Email: admin@querylens.ai")
        print("  Password: Admin123!")
        print("  Connected Database: E-Commerce & Operations DB (7 tables introspected)")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
