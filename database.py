"""
Database connection for MongoDB Compass (localhost)
"""

import os
from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        # Use local MongoDB from Compass
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        print(f" Connecting to: {self.mongo_uri}")
        
        self.client = None
        self.db = None
        self.fs = None
        self.users_col = None
        self.food_logs_col = None
        
        self._connect()
    
    def _connect(self):
        """Connect to local MongoDB"""
        try:
            # Simple connection to local MongoDB
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            print(" MongoDB connected successfully!")
            
            # Use our database
            self.db = self.client["nutrilens_db"]
            print(f" Database: {self.db.name}")
            
            # Setup GridFS for images
            self.fs = GridFS(self.db)
            
            # Get collections
            self.users_col = self.db["users"]
            self.food_logs_col = self.db["food_logs"]
            
            print(f" Users collection: Ready")
            print(f" Food logs collection: Ready")
            
        except Exception as e:
            print(f" MongoDB connection failed: {e}")
            print("\n Please run: python setup_database.py first!")
            raise
    
    def get_next_user_id(self):
        """Get next auto-incrementing user ID"""
        try:
            last_user = self.users_col.find_one(
                sort=[("user_id_number", -1)]
            )
            if last_user and "user_id_number" in last_user:
                return last_user["user_id_number"] + 1
            return 1
        except:
            return 1
    
    def save_profile_image(self, user_id, image_bytes):
        """Save profile image to GridFS"""
        try:
            # Remove old image if exists
            old_file = self.fs.find_one({"filename": f"{user_id}_profile.png"})
            if old_file:
                self.fs.delete(old_file._id)
            
            # Save new image
            fs_id = self.fs.put(
                image_bytes,
                filename=f"{user_id}_profile.png",
                metadata={"user_id": user_id}
            )
            return fs_id
        except Exception as e:
            print(f" Could not save image: {e}")
            return None
    
    def get_profile_image(self, fs_id):
        """Get profile image from GridFS"""
        try:
            return self.fs.get(fs_id).read()
        except:
            return None
    
    def delete_profile_image(self, fs_id):
        """Delete profile image"""
        try:
            self.fs.delete(fs_id)
            return True
        except:
            return False

# Global database instance
db = Database()