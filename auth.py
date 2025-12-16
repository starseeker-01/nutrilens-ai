"""
Authentication module
"""

import bcrypt
from database import db

class AuthManager:
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    @staticmethod
    def check_password(password, hashed_password):
        """Verify password against hash"""
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode()
        return bcrypt.checkpw(password.encode(), hashed_password)
    
    def authenticate(self, username, password):
        """Authenticate user"""
        user = db.users_col.find_one({"username": username})
        if not user:
            return None
        if self.check_password(password, user["password_hash"]):
            return user
        return None
    
    def register_user(self, user_data):
        """Register new user"""
        try:
            # Check if email already exists
            existing = db.users_col.find_one({"email": user_data["email"]})
            if existing:
                return False, "Email already registered"
            
            # Insert user
            result = db.users_col.insert_one(user_data)
            return True, "Registration successful"
        except Exception as e:
            return False, str(e)
    
    def recover_user_id(self, email_or_name):
        """Find user by email or name"""
        if '@' in email_or_name:
            user = db.users_col.find_one({"email": email_or_name})
        else:
            user = db.users_col.find_one({"name": {"$regex": email_or_name, "$options": "i"}})
        
        return user.get("username") if user else None
    
    def reset_password(self, username, new_password):
        """Reset user password"""
        hashed = self.hash_password(new_password)
        result = db.users_col.update_one(
            {"username": username},
            {"$set": {"password_hash": hashed}}
        )
        return result.modified_count > 0
    
    def update_user_profile(self, username, update_data):
        """Update user profile"""
        result = db.users_col.update_one(
            {"username": username},
            {"$set": update_data}
        )
        return result.modified_count > 0

# Global auth instance
auth = AuthManager()