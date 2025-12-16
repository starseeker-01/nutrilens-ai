#!/usr/bin/env python3
"""
RUN THIS SCRIPT FIRST to setup MongoDB for NutriLens
"""

import sys
import os
import bcrypt
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_database():
    print("="*60)
    print("NUTRI LENS - MONGODB SETUP")
    print("="*60)
    
    # Install pymongo if not present
    try:
        from pymongo import MongoClient
        print(" PyMongo already installed")
    except ImportError:
        print(" Installing PyMongo...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo"])
        from pymongo import MongoClient
        print(" PyMongo installed successfully")
    
    # Connect to MongoDB
    try:
        print("\n Connecting to MongoDB...")
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print(" MongoDB connection successful!")
        
        # Create database
        db = client["nutrilens_db"]
        print(f" Database: {db.name}")
        
        # Create collections
        collections = ["users", "food_logs"]
        for col_name in collections:
            if col_name not in db.list_collection_names():
                db.create_collection(col_name)
                print(f" Created collection: {col_name}")
            else:
                print(f" Collection exists: {col_name}")
        
        # Create indexes
        users_col = db["users"]
        food_logs_col = db["food_logs"]
        
        # User indexes
        users_col.create_index("username", unique=True)
        users_col.create_index("email", unique=True)
        print(" Created user indexes")
        
        # Food log indexes
        food_logs_col.create_index([("user_id", 1), ("date", 1)])
        print(" Created food log indexes")
        
        # Count existing users
        user_count = users_col.count_documents({})
        
        # Create sample admin if no users exist
        if user_count == 0:
            print("\n Creating sample admin user...")
            
            hashed_pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
            
            admin_user = {
                "user_id_number": 1,
                "username": "admin",
                "name": "Admin User",
                "email": "admin@nutrilens.com",
                "password_hash": hashed_pw,
                "age": 30,
                "gender": "Other",
                "height_cm": 170,
                "weight_kg": 70,
                "goal": "weight_loss",
                "dietary_preference": "Veg",
                "activity_level": "Moderately Active : Moderate exercise 3–5 days/week.",
                "daily_calorie_target": 2200,
                "allergies": [],
                "registration_date": datetime.now().isoformat()
            }
            
            users_col.insert_one(admin_user)
            print("Created admin user:")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   Email: admin@nutrilens.com")
        
        # Show database status
        print("\n DATABASE STATUS:")
        print(f"   Users: {users_col.count_documents({})}")
        print(f"   Food Logs: {food_logs_col.count_documents({})}")
        
        print("\n" + "="*60)
        print(" MONGODB SETUP COMPLETE!")
        print("="*60)
        print("\n Next steps:")
        print("1. Install other requirements: pip install -r requirements.txt")
        print("2. Run the app: python run.py")
        print("3. Or: streamlit run app.py")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Make sure MongoDB is running")
        print("2. Open MongoDB Compass to verify connection")
        print("3. Check if MongoDB service is running")
        print("4. Try: 'net start MongoDB' (as Administrator)")
        return False

if __name__ == "__main__":
    setup_database()