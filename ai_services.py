"""
Gemini AI integration for food analysis
"""

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

class AIServices:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        genai.configure(api_key=api_key)
        print(" Gemini AI configured")
    
    def analyze_food_image(self, image_bytes):
        """
        Analyze food image using Gemini AI
        """
        FOOD_ANALYSIS_PROMPT = '''
        You are a nutrition expert. Analyze the meal image.
        Return ONLY valid JSON in this structure:

        {
         "foods":[
           {
             "item": "Food Name",
             "quantity": "Estimated Quantity",
             "calories": 123,
             "protein": 4,
             "fat": 2,
             "carbs": 30,
             "nutrients": ["Vitamin A", "Calcium"]
           }
         ],
         "total_calories": 400
        }

        No extra text, no explanation. Only JSON.
        '''
        
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([FOOD_ANALYSIS_PROMPT, pil_img])
            txt = response.text or ""
            
            # Extract JSON from response
            match = re.search(r"\{.*\}", txt, flags=re.S)
            if not match:
                return {"error": "JSON not found", "raw": txt}
            
            return json.loads(match.group(0))
        except Exception as e:
            return {"error": str(e)}
    
    def generate_recommendation(self, user_doc, log_doc):
        """
        Generate next meal recommendation
        """
        total_today = sum([int(m.get("total_calories", 0)) for m in log_doc.get("meals", [])])
        remaining = int(user_doc.get("daily_calorie_target", 0)) - total_today
        
        prompt = f'''
        You are a nutrition expert. Based on user's profile and today's meals, suggest the next meal.
        Return ONLY in this exact format:

        Next Meal: [Meal Type - Meal Name]
        Calories: [Approximate calories]
        Food Items:
        - [Food item 1]
        - [Food item 2]
        - [Food item 3]
        Ingredients:
        - [Ingredient 1]
        - [Ingredient 2]
        - [Ingredient 3]

        User Profile:
        - Name: {user_doc.get("name")}
        - Goal: {user_doc.get("goal")}
        - Dietary Preference: {user_doc.get("dietary_preference", "none")}
        - Daily Calorie Target: {user_doc.get("daily_calorie_target", 1500)}
        - Remaining Calories: {remaining}

        Today's meals so far:
        {[m.get('meal_name', 'Unknown') for m in log_doc.get('meals', [])]}

        Keep it short. Only meal name, calories, food items, and ingredients in bullet points.
        '''
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt])
            return response.text
        except Exception as e:
            return f"Error: {e}"

# Global AI service instance
ai_service = AIServices()