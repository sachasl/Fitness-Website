# Import all necessary libraries
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from modules import *
from datetime import timedelta, datetime, timezone
from flask_migrate import Migrate

# Create a Flask application instance
app = Flask(__name__)

# Create encyption and lifetime for sessions
app.secret_key = 'secret'
app.permanent_session_lifetime = timedelta(days=5)

# Create database called database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and migration support for the Flask app
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define the User model representing user data in the database
class User(db.Model):
    # User's general details
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    weight = db.Column(db.Float, default=90)
    height = db.Column(db.Float, default=1.75)
    age = db.Column(db.Integer, default=48)
    gender = db.Column(db.String(10), default='male')

    # Users calulated details
    bmi = db.Column(db.Float)
    bmr = db.Column(db.Float)
    tdee = db.Column(db.Float)
    exercise_level = db.Column(db.String(20), default='sedentary')
    goal = db.Column(db.String(20), default='maintain')
    intensity = db.Column(db.String(20))
    caloriesRequired = db.Column(db.Float)

    # Macronutrient ratios (percentage breakdown)
    proteinRatio = db.Column(db.Float)
    fatRatio = db.Column(db.Float)
    carbRatio = db.Column(db.Float)

    # Macronutrient requirements (in grams)
    proteinRequired = db.Column(db.Float)
    fatRequired = db.Column(db.Float)
    carbRequired = db.Column(db.Float)
    
    # Remaining macronutrients (after consuming meals)
    caloriesRemaining = db.Column(db.Float)
    proteinRemaining = db.Column(db.Float)
    fatRemaining = db.Column(db.Float)
    carbRemaining = db.Column(db.Float)

    # Keep track of new days
    last_reset = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())

    # Initializes a new User instance with default attributes
    def __init__(self, username):
        self.username = username
        self.weight = 90
        self.height = 1.75
        self.age = 48
        self.gender = 'male'
        self.bmi = calculateBMI(self.weight, self.height)
        self.bmr = calculateBMR(self.weight, self.height, self.age, self.gender)
        self.tdee = calculateTDEE(self.bmr, self.exercise_level)
        self.exercise_level = 'sedentary'
        self.goal = 'maintain'
        self.intensity = None
        self.caloriesRequired = self.tdee
        proteinRatio = self.proteinRatio
        fatRatio = self.fatRatio
        carbRatio = self.carbRatio
        proteinRequired = self.proteinRequired
        fatRequired = self.fatRequired
        carbRequired = self.carbRequired

    # Resets the user's remaining macronutrients and calorie count at the start of a new day
    def reset_macros(self):
        today = datetime.now(timezone.utc).date()

        # Ensure macros are initialized for new users
        if self.caloriesRemaining is None:
            self.caloriesRemaining = self.caloriesRequired or 0
        if self.proteinRemaining is None:
            self.proteinRemaining = self.proteinRequired or 0
        if self.fatRemaining is None:
            self.fatRemaining = self.fatRequired or 0
        if self.carbRemaining is None:
            self.carbRemaining = self.carbRequired or 0
        if self.last_reset is None:
            self.last_reset = today
        
        # Reset macros at the start of a new day
        if self.last_reset != today:
            self.caloriesRemaining = self.caloriesRequired
            self.proteinRemaining = self.proteinRequired
            self.fatRemaining = self.fatRequired
            self.carbRemaining = self.carbRequired
            self.last_reset = today
            db.session.commit()

    # Relationship to UserMeals
    meals = db.relationship('UserMeals', backref='user', lazy=True, cascade="all, delete-orphan")

# Represents a meal in the database, storing nutritional information
class Meal(db.Model):
    # All the attributes linked to a meal in the database
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(100), unique=True, nullable=False)
    measure = db.Column(db.String(50), nullable=True)
    grams = db.Column(db.Float, nullable=True)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    sat_fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(50), nullable=True)

    # Initializes a new Meal instance.
    def __init__(self, food_name, measure, grams, calories, protein, fat, sat_fat, fiber, carbs, category):
        self.food_name = food_name
        self.measure = measure
        self.grams = grams
        self.calories = calories
        self.protein = protein
        self.fat = fat
        self.sat_fat = sat_fat
        self.fiber = fiber
        self.carbs = carbs
        self.category = category

    # Relationship to UserMeals: Links meals to user consumption records
    users = db.relationship('UserMeals', backref='meal', lazy=True)

class UserMeals(db.Model):
    # Stores meals consumed by users with the details
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    amount = db.Column(db.Float, default=100)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Initializes a new User Meal instance
    def __init__(self, user_id, meal_id, amount, calories, protein, carbs, fat):
        self.user_id = user_id
        self.meal_id = meal_id
        self.amount = amount
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat
        
# Login page
@app.route('/login', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def login():
    # Create User session when user pressed login
    if request.method == 'POST':
        session.permanent = True 
        username = request.form['username'].strip().lower()
        session ['username'] = username
        
        # Check if User exists in the database
        found_user = User.query.filter_by(username=username).first()
        
        if found_user:
            # Log in existing User
            session['username'] = found_user.username
        else:
            # Create new User
            new_user = User(username)
            db.session.add(new_user)
            db.session.commit()

        # Redirect User to dashboard once logged in
        flash('Login Successful!', 'success')
        return redirect(url_for('dashboard'))
    
    else:
        # If User is already logged in, redirect to dashboard
        if 'username' in session:
            flash('Already logged in', 'info')
            return redirect(url_for('dashboard'))
        
        return render_template('login.html')

# Dashboard page
@app.route('/dashboard')
def dashboard():
    # Validation to make sure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the logged-in user from the database using the session username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # Redirect new users to account setup
    if not user_details_complete(found_user):
        flash("Please complete your account details before using the program.", "warning")
        return redirect(url_for('account'))
    
    # Get today's date in UTC
    today = datetime.now(timezone.utc).date()

    # Query to get user's meals for today
    user_meals = (
        db.session.query(UserMeals, Meal)
        .join(Meal)
        .filter(UserMeals.user_id == found_user.id)
        .filter(UserMeals.date_added >= today)
        .all()
    )

    # Render the dashboard page with the logged-in user's information
    return render_template('dashboard.html', 
                           username=username, 
                           user_db=found_user,
                           user_meals=user_meals
                           )

# Meals page
@app.route('/meals', methods=['POST', 'GET'])
def meals():
    # Validation to make sure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get the logged-in user from the database using the session username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # Redirect new users to account setup
    if not user_details_complete(found_user):
        flash("Please complete your account details before using the program.", "warning")
        return redirect(url_for('account'))

    # Reset macros if the day has changed
    found_user.reset_macros()

    # Get all meals from the database
    meals_list = Meal.query.all()

    # Get today's date in UTC
    today = datetime.now(timezone.utc).date()

    # Get meals already chosen by the user today
    user_meals = (
        db.session.query(UserMeals, Meal)
        .join(Meal)
        .filter(UserMeals.user_id == found_user.id)
        .filter(UserMeals.date_added >= today)  # Filter meals added today
        .all()
    )

    # Check if the user has reached a goal
    goal_messages = check_goal_achievement(found_user)

    # If the user submits a meal
    if request.method == 'POST':
        
        # Get the selected meal ID and amount
        meal_id = request.form.get('meal_id')
        amount = float(request.form.get('amount', 100))

        # Retrieve the selected meal from the database if a meal ID is provided
        if meal_id:
            selected_meal = Meal.query.get(meal_id)

            # Ensure valid meal selection
            if selected_meal and selected_meal.grams > 0:
                # Calculate macronutrients based on the selected amount
                calories = round((selected_meal.calories / selected_meal.grams) * amount)
                protein = round((selected_meal.protein / selected_meal.grams) * amount)
                carbs = round((selected_meal.carbs / selected_meal.grams) * amount)
                fat = round((selected_meal.fat / selected_meal.grams) * amount)

                # Update user's remaining macros, ensuring values do not go below zero
                found_user.caloriesRemaining = max(0, found_user.caloriesRemaining - calories)
                found_user.proteinRemaining = max(0, found_user.proteinRemaining - protein)
                found_user.carbRemaining = max(0, found_user.carbRemaining - carbs)
                found_user.fatRemaining = max(0, found_user.fatRemaining - fat)

                # Save the meal selection to UserMeals table
                user_meal = UserMeals(user_id=found_user.id, 
                                      meal_id=selected_meal.id, 
                                      amount=amount, 
                                      calories=calories, 
                                      protein=protein, 
                                      carbs=carbs, 
                                      fat=fat
                                      )
                db.session.add(user_meal)
                db.session.commit()

                # Flash success messages to inform the user about the added meal and its nutritional values
                flash(f"Added {amount}g of {selected_meal.food_name}  to your meals!", "success")
                flash(f"Your meal included: {calories:.2f} kcal, {protein:.2f}g protein, 
                      {carbs:.2f}g carbs, {fat:.2f}g fat", "success")
                # Refresh the page
                return redirect(url_for('meals'))  
                
            # Flash an error message if the selected meal data is missing or invalid
            else:
                flash("Meal data is missing or invalid. Please try again.", "error")

    # Render the meals page with available meals, user meals, user data, and goal messages
    return render_template('meals.html', 
                           meals_list=meals_list, 
                           user_meals=user_meals, 
                           user_db=found_user, 
                           goal_messages=goal_messages
                           )

# Goals page
@app.route('/goals', methods=['POST', 'GET'])
def goals():
    # Validation to make sure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the logged-in user from the database using the session username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # Redirect new users to account setup
    if not user_details_complete(found_user):
        flash("Please complete your account details before setting goals.", "warning")
        return redirect(url_for('account'))

    # Retrieve user's current goal settings
    goal = found_user.goal
    intensity = found_user.intensity
    caloriesRequired = found_user.caloriesRequired
    warning = None

    # If the user presses a submit button
    if request.method =='POST':
        action = request.form.get('action')
        
        # If the user submits their goals
        if action == 'updateGoals':
            # Get the users goal and intensity (if required)
            goal = request.form.get('goal')
            intensity = request.form.get('intensity')

            # Ensure user has selected a goal
            if not goal:
                flash("Please select a goal.", "error")
                return redirect(url_for('goals'))

            # Ensure intensity is selected for deficit/surplus
            if goal in ['deficit', 'surplus'] and not intensity:
                flash("Please select an intensity level for deficit or surplus.", "error")
                return redirect(url_for('goals'))

            # Retrieve the user's TDEE from database
            tdee = found_user.tdee

            # Calculate users calorie goal
            caloriesRequired, warning = calculateCalorieGoals(tdee, goal, intensity)
            if warning:
                flash(warning, "warning")

            # # Update user's goal, intensity, and calorie requirement in the database
            found_user.goal = goal
            found_user.intensity = intensity
            found_user.caloriesRequired = caloriesRequired
            db.session.commit()

            # Flash success message and redirect to the goals page
            flash(f"Goal updated to {goal} with {intensity if intensity else 'no'} intensity.", "success")
            return redirect(url_for('goals'))
        
        # If the user submits their macronutrient split
        if action == 'updateMacros':
            # Retrieve macronutrient ratio inputs from the sliders
            protein_ratio = int(request.form.get('protein'))
            fat_ratio = int(request.form.get('fat'))
            carb_ratio = int(request.form.get('carb'))

            # Update the database with the macronutrient ratio
            found_user.proteinRatio = protein_ratio
            found_user.fatRatio = fat_ratio
            found_user.carbRatio = carb_ratio

            # Ensure the ratios sum up to 100%
            if protein_ratio + fat_ratio + carb_ratio != 100:
                flash("The total of protein, fat, and carbohydrates must equal 100%.", "error")
                return redirect(url_for('goals'))

            # Check if caloriesRequired exists
            if not caloriesRequired or caloriesRequired == 0:
                flash("Calorie requirement not set. Please update your goal first.", "error")
                return redirect(url_for('goals'))

            # Convert macronutrient calories to grams
            protein_grams = round((caloriesRequired * (protein_ratio / 100)) / 4)
            fat_grams = round((caloriesRequired * (fat_ratio / 100)) / 9)
            carb_grams = round((caloriesRequired * (carb_ratio / 100)) / 4)

            # Store macronutrient values (in grams) to the database
            found_user.proteinRequired = protein_grams
            found_user.fatRequired = fat_grams
            found_user.carbRequired = carb_grams
            db.session.commit()

            # Confirm macronutrient goals update and reload page
            flash(f"Macronutrient goals updated: {protein_grams:.1f}g protein, 
                  {fat_grams:.1f}g fat, {carb_grams:.1f}g carbs", "success")
            return redirect(url_for('goals'))

    # Render the goals page with the user's current goal
    return render_template('goals.html', goal=goal)

# Activity page
@app.route('/activity')
def activity():
    # Validation to make sure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the logged-in user from the database using the session username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # Redirect new users to account setup
    if not user_details_complete(found_user):
        flash("Please complete your account details before setting goals.", "warning")
        return redirect(url_for('account'))
    
    # Render the activity page
    return render_template('activity.html')

# Calories page
@app.route('/calories')
def calories():
    # Validation to make sure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the logged-in user from the database using the session username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # Redirect new users to account setup
    if not user_details_complete(found_user):
        flash("Please complete your account details before setting goals.", "warning")
        return redirect(url_for('account'))
    
    # Render the calories page
    return render_template('calories.html')

# Account page
@app.route('/account', methods=['POST', 'GET'])
def account():
    # Validation to make sure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the logged-in user from the database using the session username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # If the user presses a submit button
    if request.method == 'POST':
        # Retrieve the action specified in the form submission
        action = request.form.get('action')

        # Create an empty list to allow for messsage flashes to be together
        messages = []

        # If the user presses the submit button in the user details section
        if action == 'updateDetails':
            # Get user details from the form submission
            new_weight = request.form.get('getWeight')
            new_height = request.form.get('getHeight')
            new_age = request.form.get('getAge')
            new_gender = request.form.get('gender', 'male')
            new_exercise_level = request.form.get('exercise_level')

            # Flags to track if any user details have changed
            weight_changed = False
            height_changed = False
            age_changed = False
            gender_changed = False
            exercise_changed = False
            bmr_changed = False

            # Check and update user details if they have changed
            if new_weight and float(new_weight) != found_user.weight:
                found_user.weight = float(new_weight)
                messages.append(f"Weight updated to {new_weight} kg")
                weight_changed = True

            if new_height and float(new_height) != found_user.height:
                found_user.height = float(new_height)
                messages.append(f"Height updated to {new_height} m")
                height_changed = True

            if new_age and int(new_age) != found_user.age:
                found_user.age = int(new_age)
                messages.append(f"Age updated to {new_age} years")
                age_changed = True

            if new_gender != found_user.gender:
                found_user.gender = new_gender
                messages.append(f"Gender updated to {new_gender}")
                gender_changed = True
            
            if new_exercise_level != found_user.exercise_level:
                found_user.exercise_level = request.form.get('exercise_level')
                messages.append(f"Exercise level updated to {found_user.exercise_level.replace('_', ' ').title()}")
                exercise_changed = True

            # Update BMI only if weight or height changed
            if weight_changed or height_changed:
                found_user.bmi = calculateBMI(found_user.weight, found_user.height)

            # Update BMR only if weight, height, age, or gender changed
            if weight_changed or height_changed or age_changed or gender_changed:
                found_user.bmr = calculateBMR(found_user.weight, found_user.height, found_user.age, found_user.gender)
                bmr_changed = True

            # Update TDEE only if BMR or exercise level changed
            if exercise_changed or bmr_changed:
                found_user.tdee = calculateTDEE(found_user.bmr, found_user.exercise_level)

                # Recalculate caloriesRequired when TDEE changes
                found_user.caloriesRequired, warning = calculateCalorieGoals(found_user.tdee, found_user.goal, found_user.intensity)

                # Retrieve the macro ratios from the database
                protein_ratio = found_user.proteinRatio if found_user.proteinRatio else 25
                fat_ratio = found_user.fatRatio if found_user.fatRatio else 30
                carb_ratio = found_user.carbRatio if found_user.carbRatio else 45


                # Recalculate macronutrient goals as caloriesRequired has changed
                found_user.proteinRequired = round((found_user.caloriesRequired * (protein_ratio / 100)) / 4)
                found_user.fatRequired = round((found_user.caloriesRequired * (fat_ratio / 100)) / 9)
                found_user.carbRequired = round((found_user.caloriesRequired * (carb_ratio / 100)) / 4)
                
            # Only flash messages if something actually changed
            if messages:
                flash(", ".join(messages), "success")

            # Commit changes to the database
            db.session.commit()
        
        # If user presses the logout button
        if action == 'logout':
            # Log out the user and clear the session
            flash('You have been logged out!', 'success')
            session.pop('username', None)

            # Redirect the user to the login page
            return redirect(url_for('login'))

        # If user presses the delete account button
        if action == 'delete':
            # Delete the user from the database and clear their session
            db.session.delete(found_user)
            db.session.commit()
            session.pop('username', None)
            flash('Account deleted successfully!', 'success')

            # Redirect the user to the login page
            return redirect(url_for('login'))

    # Render the account page with user details
    return render_template(
        'account.html', username=username, user_db=found_user)

# Run the Flask application and ensure database tables are created
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
