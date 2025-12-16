"""
Setup script to initialize the SQLite database and create default users.
Run this once before starting the app.
"""
from utils.db import init_db
from utils.auth import create_user
import sys

def setup():
    print("🔄 Initializing database...")
    try:
        init_db()
        print("✅ Database tables created.")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)

    print("👤 Creating default admin user...")
    if create_user("Admin", "Admin@123", "admin"):
        print("✅ Admin user created (Admin / Admin@123)")
    else:
        print("ℹ️ Admin user already exists or error occurred.")

    print("\n🎉 Setup complete! You can now run the app:")
    print("streamlit run app.py")

if __name__ == "__main__":
    setup()
