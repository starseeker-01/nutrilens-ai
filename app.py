"""
NUTRI LENS - AI Nutrition Assistant
Complete Streamlit Application
"""
import os
import io
import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
from datetime import date, datetime, timedelta

# Import your modular components
try:
    from database import db
    from auth import auth
    from ai_services import ai_service
    from utils import NutritionCalculator, DataManager
    
    print(" All modules loaded successfully")
    
except ImportError as e:
    st.error(f" Import Error: {e}")
    st.info("""
    Please make sure all required files are in the same directory:
    - database.py
    - auth.py  
    - ai_services.py
    - utils.py
    """)
    st.stop()

# PAGE CONFIGURATION
st.set_page_config(
    page_title="NutriLens",
    page_icon="🍽️",
    layout="wide"
)

# SESSION STATE INITIALIZATION
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.edit_mode = False

# HELPER FUNCTIONS
def logout():
    """Logout user and clear session"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.edit_mode = False
    st.rerun()

def display_logo():
    """Display application logo"""
    logo_paths = [
        "assets/nutri logo.png",
        "nutri logo.png",
        "assets/logo.png",
        "logo.png"
    ]
    
    for logo_path in logo_paths:
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                st.image(logo_img, width=260)
                return
            except Exception:
                continue
    
    # If no logo found, show placeholder
    st.info("Upload 'nutri logo.png' to the assets folder")


# AUTHENTICATION PAGES
def show_login_page():
    """Display login page with tabs"""
    display_logo()
    st.title("Snap.Detect.Eat Smart")
    
    if not st.session_state.logged_in:
        # Show Login and Register tabs when not logged in
        login_tab, register_tab = st.tabs([" Login", " Register"])

        # TAB 1 — LOGIN
        with login_tab:
            st.header("Login to Your Account")

            col1, col2 = st.columns([2, 1])

            with col1:
                with st.form("login_form"):
                    username = st.text_input("Username / User ID")
                    password = st.text_input("Password", type="password")
                    submit_login = st.form_submit_button("Login")

                    if submit_login:
                        if not username or not password:
                            st.error("Please enter both username and password")
                        else:
                            user_doc = auth.authenticate(username, password)
                            if user_doc:
                                st.session_state.logged_in = True
                                st.session_state.user = user_doc
                                st.success(f" Login successful! Welcome back, {user_doc.get('name', 'User')}")
                                st.rerun()
                            else:
                                st.error(" Invalid username or password")

            with col2:
                st.subheader("Need Help?")

                # Forgot Password
                with st.expander(" Forgot Password"):
                    with st.form("forgot_password_form"):
                        recover_username = st.text_input("Enter your Username")
                        new_password = st.text_input("New Password", type="password")
                        confirm_password = st.text_input("Confirm New Password", type="password")
                        reset_submit = st.form_submit_button("Reset Password")

                        if reset_submit:
                            if not recover_username:
                                st.error("Please enter your username")
                            elif not new_password or not confirm_password:
                                st.error("Please enter and confirm new password")
                            elif new_password != confirm_password:
                                st.error("Passwords do not match")
                            else:
                                if auth.reset_password(recover_username, new_password):
                                    st.success("Password reset successfully! You can now login with your new password.")
                                else:
                                    st.error("Username not found. Please check your username.")

                # Forgot User ID
                with st.expander(" Forgot User ID"):
                    with st.form("forgot_userid_form"):
                        email_name = st.text_input("Enter your Email or Full Name")
                        recover_submit = st.form_submit_button("Recover User ID")

                        if recover_submit:
                            if not email_name:
                                st.error("Please enter your email or name")
                            else:
                                user_id = auth.recover_user_id(email_name)
                                if user_id:
                                    st.success(f"Your User ID is: **{user_id}**")
                                    st.info("Please use this to login")
                                else:
                                    st.error("No account found with that email or name")

        # TAB 2 — REGISTER
        with register_tab:
            st.header("Register New User")

            # Get next user ID
            next_number = db.get_next_user_id()
            st.info(f"Your auto-generated User ID will be: **user{next_number}**")

            # Registration Form
            with st.form("reg", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    full = st.text_input("Full Name*", placeholder="Enter your full name", key="reg_fullname")
                    age = st.number_input("Age*", 1, 120, 25, key="reg_age")
                    gender = st.selectbox("Gender*", ["Male", "Female", "Other"], key="reg_gender")
                    height = st.number_input("Height (cm)*", 50, 250, 160, key="reg_height")
                    weight = st.number_input("Weight (kg)*", 20, 200, 60, key="reg_weight")
                    email = st.text_input("Email*", placeholder="your.email@example.com", key="reg_email")

                with col2:
                    dietary_pref = st.selectbox("Dietary Preference*", ["Veg", "Non-Veg"], key="reg_diet")
                    goal = st.selectbox("Goal*", ["weight_loss", "maintenance", "weight_gain"], key="reg_goal")

                    # Activity Level options with full descriptions
                    activity_options = [
                        "Sedentary : Little or no exercise, mostly sitting.",
                        "Lightly Active : Light exercise or walking 1–3 days/week.",
                        "Moderately Active : Moderate exercise 3–5 days/week.",
                        "Very Active : Heavy exercise or sports 6–7 days/week."
                    ]

                    activity_selected = st.selectbox(
                        "Activity Level*",
                        options=activity_options,
                        help="Select your daily activity level",
                        key="activity_level_register"
                    )

                    allergies = st.text_input("Allergies (comma-separated)", placeholder="peanuts, milk, gluten", key="reg_allergies")
                    password = st.text_input("Password*", type="password", key="reg_password")
                    confirm_password = st.text_input("Confirm Password*", type="password", key="reg_confirm_password")
                    profile_img = st.file_uploader("Profile Image (.jpg/.png)", type=["jpg", "png"], key="reg_profile_img")

                st.caption("* Required fields")

                submit = st.form_submit_button("Create Account", key="reg_submit")

            # Handle form submission
            if submit:
                # Validate required fields
                required_fields = [full, email, password, confirm_password]
                if not all(required_fields):
                    st.error("Please fill all required fields (*)")
                elif password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    # Check if email already exists
                    existing_user = db.users_col.find_one({"email": email})
                    if existing_user:
                        st.error("Email already registered. Please use a different email or login.")
                    else:
                        # Process allergies
                        allergy_list = [a.strip().lower() for a in allergies.split(",")] if allergies else []

                        # Calculate daily calories using NutritionCalculator
                        daily_target = NutritionCalculator.calculate_daily_calories(
                            age, gender, height, weight, activity_selected, goal
                        )

                        # Prepare user document
                        auto_userid = f"user{next_number}"
                        user_doc = {
                            "user_id_number": next_number,
                            "username": auto_userid,
                            "name": full,
                            "email": email,
                            "age": age,
                            "gender": gender,
                            "height_cm": height,
                            "weight_kg": weight,
                            "goal": goal,
                            "dietary_preference": dietary_pref,
                            "activity_level": activity_selected,
                            "daily_calorie_target": daily_target,
                            "password_hash": auth.hash_password(password),
                            "allergies": allergy_list,
                            "registration_date": datetime.now().isoformat()
                        }

                        # Save profile image if provided
                        if profile_img:
                            fs_id = db.save_profile_image(auto_userid, profile_img.read())
                            if fs_id:
                                user_doc["profile_img_id"] = fs_id

                        # Insert user in MongoDB
                        try:
                            success, message = auth.register_user(user_doc)
                            if success:
                                st.success(f" Account created successfully!")
                                st.balloons()
                                st.info(f"**Your Login Credentials:**")
                                st.write(f"**User ID:** `{auto_userid}`")
                                st.write(f"**Email:** `{email}`")
                                st.write(f"**Password:** (the one you set)")
                                st.write("Please go to the Login tab to access your account.")
                            else:
                                st.error(f"Registration failed: {message}")
                        except Exception as e:
                            st.error(f"Registration failed: {str(e)}")

# MAIN APPLICATION PAGES (Logged In)
def show_main_app():
    """Display main application after login"""
    welcome_user = st.session_state.user.get('name', 'User')
    st.success(f" Welcome, {welcome_user}! | User ID: {st.session_state.user.get('username', 'N/A')}")

    # Main tabs for logged in users
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        " Upload Meal",
        " Profile",
        " Today",
        " Last 7 Days",
        " Logout"
    ])

    # TAB 1 — UPLOAD MEAL
    with tab1:
        st.header(" Upload Meal for Analysis")
        user_id = st.session_state["user"]["username"]

        col1, col2 = st.columns([1, 1])

        with col1:
            with st.form("upload_meal_form"):
                st.subheader("Meal Details")
                meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
                meal_image = st.file_uploader("Upload Meal Image", type=["jpg", "png", "jpeg"])
                notes = st.text_area("Additional Notes (Optional)", placeholder="Any special notes about this meal...")

                submit_upload = st.form_submit_button(" Analyze & Save Meal", use_container_width=True)

        with col2:
            st.subheader(" How it works:")
            st.markdown('''
            1. **Select** your meal type
            2. **Upload** a clear photo of your meal
            3. **Click** Analyze & Save
            4. Get **instant nutrition analysis**

             NutriLens-AI will detect:
            - Food items
            - Estimated quantities
            - Calories & nutrients
            ''')

        if submit_upload:
            if not meal_image:
                st.error("Please upload an image before submitting.")
            else:
                # Read image bytes
                image_bytes = meal_image.read()

                with st.spinner(" Analyzing your meal..."):
                    parsed = ai_service.analyze_food_image(image_bytes)

                if "error" in parsed:
                    st.error(f"Failed to analyze image: {parsed.get('error')}")
                else:
                    st.success(" Meal analyzed successfully!")

                    # Display results
                    st.subheader(" Analysis Results")

                    # Create DataFrame for display
                    foods_data = []
                    for food in parsed.get("foods", []):
                        foods_data.append({
                            "Food Item": food.get("item", "Unknown"),
                            "Quantity": food.get("quantity", "N/A"),
                            "Calories": f"{food.get('calories', 0)} kcal",
                            "Protein": f"{food.get('protein', 0)}g",
                            "Carbs": f"{food.get('carbs', 0)}g",
                            "Fat": f"{food.get('fat', 0)}g"
                        })

                    if foods_data:
                        df = pd.DataFrame(foods_data)
                        st.dataframe(df, use_container_width=True)

                    # Display total calories
                    total_cal = parsed.get("total_calories", 0)
                    st.metric("Total Meal Calories", f"{total_cal} kcal")

                    # Add notes to parsed data
                    if notes:
                        parsed["notes"] = notes

                    # Save meal to DB using DataManager
                    DataManager.save_meal_log(user_id, meal_type, parsed, notes)
                    st.info(f" {meal_type} saved to your food log!")

                    # Show SIMPLE recommendation
                    log_doc = DataManager.get_today_log(user_id)
                    if log_doc:
                        with st.expander(" Next Meal Recommendation", expanded=True):
                            recommendation_text = ai_service.generate_recommendation(st.session_state["user"], log_doc)

                            # Format the response for better display
                            lines = recommendation_text.split('\n')
                            for line in lines:
                                if line.startswith('Next Meal:'):
                                    st.subheader(line)
                                elif line.startswith('Calories:'):
                                    st.metric("Approximate Calories", line.replace('Calories: ', ''))
                                elif line.startswith('Food Items:'):
                                    st.write("**Food Items:**")
                                elif line.startswith('Ingredients:'):
                                    st.write("**Ingredients:**")
                                elif line.startswith('-'):
                                    st.write(line)
                                elif line.strip():
                                    st.write(line)

    # TAB 2 — PROFILE
    with tab2:
        st.header(" My Profile")
        u = st.session_state["user"]

        # Initialize edit mode in session
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False

        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            st.subheader("Profile Image")
            if u.get("profile_img_id"):
                try:
                    img_data = db.get_profile_image(u["profile_img_id"])
                    if img_data:
                        img = Image.open(io.BytesIO(img_data))
                        st.image(img, width=200)
                except:
                    st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=150)
            else:
                st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=150)
                st.caption("No profile image uploaded")

            # Upload new profile image
            new_img = st.file_uploader("Update Profile Image", type=["jpg", "png"], key="profile_img_upload")
            if new_img and st.button("Update Image", key="update_img_btn"):
                try:
                    # Delete old image if exists
                    if u.get("profile_img_id"):
                        db.delete_profile_image(u["profile_img_id"])

                    # Save new image
                    fs_id = db.save_profile_image(u['username'], new_img.read())
                    if fs_id:
                        db.users_col.update_one(
                            {"username": u["username"]},
                            {"$set": {"profile_img_id": fs_id}}
                        )
                        st.session_state["user"]["profile_img_id"] = fs_id
                        st.success("Profile image updated!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to update image: {str(e)}")

        with col2:
            st.subheader("Personal Information")

            # Edit/Save Button
            col_edit1, col_edit2 = st.columns([3, 1])

            with col_edit1:
                if st.button(" Edit Profile" if not st.session_state.edit_mode else "💾 Save Changes",
                            type="primary" if st.session_state.edit_mode else "secondary",
                            key="edit_profile_btn"):
                    if st.session_state.edit_mode:
                        # Exit edit mode without saving (form handles saving)
                        st.session_state.edit_mode = False
                        st.rerun()
                    else:
                        # Enter edit mode
                        st.session_state.edit_mode = True
                        st.rerun()

            # Display info
            if st.session_state.edit_mode:
                # EDIT MODE - Form to edit profile info
                with st.form("edit_profile_form"):
                    # Store form values in variables
                    edit_name = st.text_input("Full Name", value=u.get('name',''), key="edit_name")
                    edit_age = st.number_input("Age", min_value=1, max_value=120, value=u.get('age',25), key="edit_age")

                    # Gender - Display only (not editable)
                    st.write(f"**Gender:** {u.get('gender', 'N/A')} (Cannot be changed)")

                    edit_height = st.number_input("Height (cm)", min_value=50, max_value=250, value=u.get('height_cm',160), key="edit_height")
                    edit_weight = st.number_input("Weight (kg)", min_value=20, max_value=200, value=u.get('weight_kg',60), key="edit_weight")

                    edit_dietary_pref = st.selectbox("Dietary Preference", ["Veg", "Non-Veg"],
                                                   index=0 if u.get('dietary_preference', 'Veg') == 'Veg' else 1,
                                                   key="edit_diet")

                    edit_goal = st.selectbox("Goal", ["weight_loss", "maintenance", "weight_gain"],
                                           index=["weight_loss", "maintenance", "weight_gain"].index(u.get('goal', 'weight_loss')),
                                           key="edit_goal")

                    # Activity Level options
                    activity_options = [
                        "Sedentary : Little or no exercise, mostly sitting.",
                        "Lightly Active : Light exercise or walking 1–3 days/week.",
                        "Moderately Active : Moderate exercise 3–5 days/week.",
                        "Very Active : Heavy exercise or sports 6–7 days/week."
                    ]

                    current_activity = u.get('activity_level', 'Sedentary : Little or no exercise, mostly sitting.')

                    # Find the matching option
                    current_index = 0  # Default to first option
                    for i, option in enumerate(activity_options):
                        # Check if current activity matches any option
                        if current_activity in option or option in current_activity:
                            current_index = i
                            break

                    edit_activity = st.selectbox(
                        "Activity Level",
                        options=activity_options,
                        index=current_index,
                        key="edit_activity"
                    )

                    # Allergies
                    current_allergies = ", ".join(u.get('allergies', [])) if u.get('allergies') else ""
                    edit_allergies = st.text_input("Allergies (comma-separated)", value=current_allergies,
                                                 placeholder="peanuts, milk, gluten",
                                                 key="edit_allergies")

                    # Submit Button - This will handle the actual saving
                    save_changes = st.form_submit_button(" Save All Changes", type="primary", key="edit_submit")

                    if save_changes:
                        # Recalculate TDEE based on new values (using original gender from session)
                        gender = u.get('gender', 'Male')  # Use original gender
                        new_daily_target = NutritionCalculator.calculate_daily_calories(
                            edit_age, gender, edit_height, edit_weight, edit_activity, edit_goal
                        )

                        # Process allergies
                        allergy_list = [a.strip().lower() for a in edit_allergies.split(",")] if edit_allergies else []

                        # Update user document (excluding gender)
                        update_data = {
                            "name": edit_name,
                            "age": edit_age,
                            "height_cm": edit_height,
                            "weight_kg": edit_weight,
                            "dietary_preference": edit_dietary_pref,
                            "goal": edit_goal,
                            "activity_level": edit_activity,
                            "daily_calorie_target": new_daily_target,
                            "allergies": allergy_list
                        }

                        # Update in database
                        auth.update_user_profile(u["username"], update_data)

                        # Update session state
                        for key, value in update_data.items():
                            st.session_state.user[key] = value

                        st.success(" Profile updated successfully!")
                        st.session_state.edit_mode = False
                        st.rerun()

            else:
                # VIEW MODE - Display profile info
                info_cols = st.columns(2)

                with info_cols[0]:
                    st.metric("Full Name", u.get('name','N/A'))
                    st.metric("User ID", u.get('username','N/A'))
                    st.metric("Age", f"{u.get('age','N/A')} years")
                    st.metric("Gender", u.get('gender','N/A'))

                with info_cols[1]:
                    st.metric("Height", f"{u.get('height_cm','N/A')} cm")
                    st.metric("Weight", f"{u.get('weight_kg','N/A')} kg")
                    st.metric("Diet", u.get('dietary_preference','N/A'))
                    st.metric("Goal", u.get('goal','N/A').replace('_',' ').title())

        with col3:
            st.subheader("Health Settings")

            # Add the one-line message about calorie calculation
            st.info(" Your daily calories are calculated based on your age, gender, weight, height, activity level, and goal.")

            # Daily Calorie Information (READ ONLY)
            current_target = u.get('daily_calorie_target', 1500)
            st.metric("Daily Calorie Target", f"{current_target} kcal")

            # Activity Level
            activity = u.get('activity_level', 'N/A')
            st.write(f"**Activity Level:** {activity}")

            # Allergies
            allergies = u.get("allergies", [])
            if allergies:
                st.write("**Allergies:**")
                for allergy in allergies:
                    st.write(f"- {allergy.title()}")
            else:
                st.write("**Allergies:** None registered")

            # Additional health metrics
            st.divider()
            st.subheader(" Health Metrics")

            # Calculate BMI using NutritionCalculator
            bmi = NutritionCalculator.calculate_bmi(
                u.get('height_cm', 0),
                u.get('weight_kg', 0)
            )

            if bmi > 0:
                # Display BMI with context
                col_bmi1, col_bmi2 = st.columns([1, 2])
                with col_bmi1:
                    st.metric("BMI Score", f"{bmi:.1f}")

                with col_bmi2:
                    # Get BMI category
                    category, color_type = NutritionCalculator.get_bmi_category(bmi)
                    
                    if color_type == "info":
                        st.info(f'''
                        **Health Status: {category}**

                        *Suggestion:* Consider increasing calorie intake with nutrient-dense foods
                        ''')
                    elif color_type == "success":
                        st.success(f'''
                        **Health Status: {category}**

                        *Suggestion:* Maintain healthy habits with balanced nutrition
                        ''')
                    elif color_type == "warning":
                        st.warning(f'''
                        **Health Status: {category}**

                        *Suggestion:* Small lifestyle changes can help reach a healthier weight
                        ''')
                    else:
                        st.error(f'''
                        **Health Status: {category}**

                        *What this means:* Your weight may increase health risks

                        **NutriLens Can Help You:**

                         - Track meals and calories
                         - Make healthier food choices
                         - Reach your weight goals safely
                         - Monitor progress over time
                        ''')

                # Show weight goal context
                user_goal = u.get('goal', 'maintenance')
                if user_goal == 'weight_loss':
                    st.info(f'''
                    **Your Current Goal: Weight Loss** 
                    - Daily target: **{current_target} calories**
                    - App will help you create a **calorie deficit**
                    - Track your meals to stay on target
                    ''')
                elif user_goal == 'weight_gain':
                    st.info(f'''
                    **Your Current Goal: Weight Gain**
                    - Daily target: **{current_target} calories**
                    - Focus on nutrient-rich foods
                    ''')
                else:
                    st.info(f'''
                    **Your Current Goal: Maintain Weight**
                    - Daily target: **{current_target} calories**
                    - Maintain a balanced diet
                    ''')

    # TAB 3 — TODAY'S SUMMARY
    with tab3:
        st.header(" Today's Summary")
        user_id = st.session_state["user"]["username"]
        
        # Get today's log using DataManager
        log = DataManager.get_today_log(user_id)
        
        # Daily stats
        daily_target = st.session_state["user"].get("daily_calorie_target", 1500)

        if not log or not log.get("meals"):
            col1, col2 = st.columns(2)
            with col1:
                st.info("No meals logged for today yet.")
            with col2:
                st.metric("Daily Target", f"{daily_target} kcal")
        else:
            # Calculate totals
            total_calories = sum([m.get("total_calories", 0) for m in log["meals"]])
            remaining = max(0, daily_target - total_calories)

            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Calories Consumed", f"{total_calories} kcal")
            with col2:
                st.metric("Remaining Calories", f"{remaining} kcal")
            with col3:
                st.metric("Daily Target", f"{daily_target} kcal")

            # Simple target message
            st.divider()
            if total_calories <= daily_target:
                st.success(f" You are ON target! {remaining} calories remaining for today.")
            else:
                st.error(f" You are OVER target by {abs(remaining)} calories.")

            # Display meals (simple list)
            st.subheader("Today's Meals")
            for meal in log["meals"]:
                with st.expander(f"{meal['meal_name'].capitalize()} - {meal.get('time', 'N/A')} | {meal.get('total_calories', 0)} kcal"):
                    if meal.get("foods"):
                        for food in meal["foods"]:
                            st.write(f"• **{food.get('item', 'Unknown')}** - {food.get('calories', 0)} kcal")

    # TAB 4 — LAST 7 DAYS
    with tab4:
        st.header(" Last 7 Days Trend")
        user_id = st.session_state["user"]["username"]
        daily_target = st.session_state["user"].get("daily_calorie_target", 1500)
        
        # Get weekly data using DataManager
        weekly_logs = DataManager.get_weekly_data(user_id, days=7)
        df = DataManager.create_weekly_dataframe(weekly_logs, daily_target)

        if df.empty:
            st.warning("No meal data available for the last 7 days.")
        else:
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_calories = df["Calories"].mean()
                st.metric("Avg Daily Calories", f"{avg_calories:.0f} kcal")
            with col2:
                over_target_days = (df["Calories"] > daily_target).sum()
                st.metric("Days Over Target", f"{over_target_days}/7")
            with col3:
                days_with_meals = (df["Meals"] > 0).sum()
                st.metric("Active Days", f"{days_with_meals}/7")

            # Calories chart with different colors for over/under target
            st.subheader("Calories Consumption Trend")

            # Create separate dataframes for over and under target
            over_target_df = df[df["Calories"] > daily_target]
            under_target_df = df[df["Calories"] <= daily_target]

            # Base line chart
            base = alt.Chart(df).encode(
                x=alt.X("Date:T", title="Date", axis=alt.Axis(format="%b %d")),
                y=alt.Y("Calories:Q", title="Calories Consumed"),
                tooltip=["Day:N", "Calories:Q", "Status:N"]
            )

            # Line connecting all points
            line = base.mark_line(color="lightgray", strokeDash=[5, 5])

            # Points for under/at target (green)
            under_points = alt.Chart(under_target_df).mark_circle(size=100, color="green").encode(
                x="Date:T",
                y="Calories:Q",
                tooltip=["Day:N", "Calories:Q", alt.Tooltip("Status:N", title="Status")]
            )

            # Points for over target (red)
            over_points = alt.Chart(over_target_df).mark_circle(size=100, color="red").encode(
                x="Date:T",
                y="Calories:Q",
                tooltip=["Day:N", "Calories:Q", alt.Tooltip("Status:N", title="Status")]
            )

            # Daily target line
            target_line = alt.Chart(pd.DataFrame({"y":[daily_target]})).mark_rule(
                color='red', strokeDash=[5,5], strokeWidth=2
            ).encode(y='y')

            # Combine all charts
            chart = line + under_points + over_points + target_line

            # Add legend
            legend_df = pd.DataFrame({
                "Status": ["Under/At Target", "Over Target"],
                "Color": ["green", "red"]
            })

            legend = alt.Chart(legend_df).mark_circle(size=100).encode(
                y=alt.Y("Status:N", axis=alt.Axis(orient="right")),
                color=alt.Color("Color:N", scale=None, legend=None)
            )

            final_chart = chart | legend

            st.altair_chart(final_chart, use_container_width=True)
            st.caption(f"🟢 **Green dots**: At or below target | 🔴 **Red dots**: Above target | 🔴 **Dashed line**: Daily target ({daily_target} kcal)")

            # Data table with color coding
            st.subheader("Detailed Data")
            df_display = df.copy()
            df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d (%A)")

            def style_status(val):
                if "Over Target" in str(val):
                    return 'color: red; font-weight: bold'
                else:
                    return 'color: green'

            # Display styled dataframe
            styled_df = df_display[["Date", "Calories", "Meals"]].copy()
            styled_df["Status"] = df_display["Calories"].apply(
                lambda x: " Over Target" if x > daily_target else " On Target"
            )

            # Apply styling
            styled_df_display = styled_df.style.applymap(
                lambda x: 'color: red; font-weight: bold' if '⚠️' in str(x) else 'color: green',
                subset=['Status']
            )

            st.dataframe(styled_df_display, use_container_width=True)

            # Summary statistics
            with st.expander(" Weekly Summary Statistics"):
                total_cal_week = df["Calories"].sum()
                avg_cal = df["Calories"].mean()
                max_cal = df["Calories"].max()
                min_cal = df["Calories"].min()
                days_over = (df["Calories"] > daily_target).sum()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Week Calories", f"{total_cal_week:.0f} kcal")
                    st.metric("Highest Day", f"{max_cal:.0f} kcal")
                with col2:
                    st.metric("Average Daily", f"{avg_cal:.0f} kcal")
                    st.metric("Lowest Day", f"{min_cal:.0f} kcal")
                with col3:
                    st.metric("Target Compliance", f"{7-days_over}/7 days")
                    st.metric("Over Target Days", f"{days_over} days")

    # TAB 5 — LOGOUT
    with tab5:
        st.header(" Logout")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.warning("Are you sure you want to logout?")

            st.info('''
            **You will lose access to:**
            - Personal meal recommendations
            - Today's food log
            - Progress tracking
            - Profile settings
            ''')

            # Two main buttons side by side
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🔓 Confirm Logout", type="primary", use_container_width=True):
                    logout()

            with col_btn2:
                if st.button("📤 Go to Meal Upload", type="secondary", use_container_width=True):
                    st.success("Redirecting to meal upload...")
                    st.rerun()

            st.divider()

            # Navigation shortcuts
            st.write("**Quick Navigation:**")

            nav_col1, nav_col2, nav_col3 = st.columns(3)
            with nav_col1:
                if st.button(" Upload Meal", icon="🍽️", use_container_width=True):
                    st.rerun()
            with nav_col2:
                if st.button(" Today's Log", icon="📊", use_container_width=True):
                    st.rerun()
            with nav_col3:
                if st.button(" My Profile", icon="👤", use_container_width=True):
                    st.rerun()

# MAIN APP ROUTER
def main():
    """Main application router"""
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_main_app()

# RUN THE APPLICATION
if __name__ == "__main__":
    main()