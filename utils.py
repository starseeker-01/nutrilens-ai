"""
Utility functions and calculations
"""

from datetime import date, datetime, timedelta
import pandas as pd
from database import db

class NutritionCalculator:
    ACTIVITY_MULTIPLIERS = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725
    }
    
    @staticmethod
    def calculate_bmi(height_cm, weight_kg):
        """Calculate BMI"""
        if height_cm <= 0:
            return 0
        height_m = height_cm / 100
        return weight_kg / (height_m * height_m)
    
    @staticmethod
    def get_bmi_category(bmi):
        """Get BMI category"""
        if bmi < 18.5:
            return "Underweight", "info"
        elif bmi < 25:
            return "Normal Weight", "success"
        elif bmi < 30:
            return "Overweight", "warning"
        else:
            return "Above Healthy Range", "error"
    
    @staticmethod
    def calculate_daily_calories(age, gender, height, weight, activity_level, goal):
        """Calculate daily calorie target"""
        # BMR calculation (Mifflin-St Jeor Equation)
        if gender == "Male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        # Extract activity level name
        activity_name = activity_level.split(":")[0].strip() if ":" in activity_level else activity_level.strip()
        multiplier = NutritionCalculator.ACTIVITY_MULTIPLIERS.get(activity_name, 1.4)
        
        tdee = bmr * multiplier
        
        # Adjust based on goal
        if goal == "weight_loss":
            return int(tdee - 500)
        elif goal == "weight_gain":
            return int(tdee + 500)
        else:  # maintenance
            return int(tdee)

class DataManager:
    @staticmethod
    def save_meal_log(user_id, meal_type, parsed_data, notes=""):
        """Save meal to daily food log"""
        today = date.today().isoformat()
        meal = {
            "meal_name": meal_type,
            "time": datetime.now().strftime("%H:%M"),
            "foods": parsed_data.get("foods", []),
            "total_calories": parsed_data.get("total_calories", 0),
            "notes": notes
        }
        
        # Check if log exists for today
        log = db.food_logs_col.find_one({"user_id": user_id, "date": today})
        
        if log:
            # Update existing log
            db.food_logs_col.update_one(
                {"_id": log["_id"]}, 
                {"$push": {"meals": meal}}
            )
        else:
            # Create new log
            db.food_logs_col.insert_one({
                "user_id": user_id, 
                "date": today, 
                "meals": [meal]
            })
        
        return True
    
    @staticmethod
    def get_today_log(user_id):
        """Get today's food log"""
        today = date.today().isoformat()
        return db.food_logs_col.find_one({"user_id": user_id, "date": today})
    
    @staticmethod
    def get_weekly_data(user_id, days=7):
        """Get food log data for last N days"""
        today = date.today()
        start_date = today - timedelta(days=days-1)
        
        logs = db.food_logs_col.find({
            "user_id": user_id,
            "date": {"$gte": start_date.isoformat(), "$lte": today.isoformat()}
        }).sort("date", 1)
        
        return list(logs)
    
    @staticmethod
    def create_weekly_dataframe(weekly_logs, daily_target):
        """Create DataFrame for weekly analysis"""
        if not weekly_logs:
            return pd.DataFrame()
        
        data = []
        for log in weekly_logs:
            total_cal = sum([m.get("total_calories", 0) for m in log.get("meals", [])])
            data.append({
                "Date": pd.to_datetime(log["date"]),
                "Calories": total_cal,
                "Meals": len(log.get("meals", [])),
                "Status": "Over Target" if total_cal > daily_target else "Under/At Target"
            })
        
        df = pd.DataFrame(data)
        
        # Ensure all dates are present
        if not df.empty:
            all_dates = pd.date_range(start=df["Date"].min(), end=df["Date"].max(), freq='D')
            df_full = pd.DataFrame({"Date": all_dates})
            df_full = df_full.merge(df, on="Date", how="left").fillna({"Calories": 0, "Meals": 0, "Status": "Under/At Target"})
            df_full["Day"] = df_full["Date"].dt.strftime("%a, %b %d")
            return df_full
        
        return pd.DataFrame()