from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from modules import *
from datetime import timedelta, datetime
import csv

app = Flask(__name__)
# Encyption and lifetime for sessions
app.secret_key = 'secret'
app.permanent_session_lifetime = timedelta(days=5)
# Create database tables
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create database and its attributes
db = SQLAlchemy(app)

# Define User class for database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    weight = db.Column(db.Float, default=90)
    height = db.Column(db.Float, default=1.75)
    age = db.Column(db.Integer, default=48)
    gender = db.Column(db.String(10), default='male')
    bmi = db.Column(db.Float)
    bmr = db.Column(db.Float)
    tdee = db.Column(db.Float)
    exercise_level = db.Column(db.String(20), default='sedentary')
    goal = db.Column(db.String(20), default='maintain')
    intensity = db.Column(db.String(20), default=None)
    caloriesRequired = db.Column(db.Float, default=None)

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

        # Relationship to UserMeals
        meals = db.relationship('UserMeals', backref='user', lazy=True)

# Define Meal class for database
class Meal(db.Model):
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

        # Relationship to UserMeals
        users = db.relationship('UserMeals', backref='meal', lazy=True)


# UserMeals Table (Linking Users & Meals)
class UserMeals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    quantity = db.Column(db.Float, default=1)  # Number of servings
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

  
        
# Login page
@app.route('/login')
@app.route('/', methods=['POST', 'GET'])
def login(): 
    # Create User session
    if request.method == 'POST':
        session.permanent = True 
        username = request.form['username']
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
        flash('Login Successful!')
        return redirect(url_for('dashboard'))
    
    else:
        # If User is already logged in, redirect to dashboard
        if 'username' in session:
            flash('Already logged in')
            return redirect(url_for('dashboard'))
        
        return render_template('login.html')

# Dashboard page
@app.route('/dashboard')
def dashboard():
    # Renders dashboard and checks if User is logged in
    if 'username' in session:
        username = session.get('username')
        found_user = User.query.filter_by(username=username).first()
        return render_template('dashboard.html', username=username, user_db=found_user)
    else:
        return redirect(url_for('login')) 

# Meals page
@app.route('/meals')
def meals():
    return render_template('meals.html')

# Goals page
@app.route('/goals', methods=['POST', 'GET'])
def goals():
    # Get User session and their database username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # Default values
    goal = found_user.goal if found_user.goal else None
    intensity = found_user.intensity if found_user.intensity else None
    caloriesRequired = None
    warning = None

    if request.method =='POST':
        action = request.form.get('action')
        if action == 'updateGoals':
            goal = request.form.get('goal')  # Get user's goal (deficit, maintain, surplus)
            intensity = request.form.get('intensity')  # Get intensity (mild, moderate, extreme)

            # Validate inputs
            if not goal:
                flash("Please select a goal.", "error")
                return redirect(url_for('goals'))

            # Ensure intensity is chosen for deficit/surplus
            if goal in ['deficit', 'surplus'] and not intensity:
                flash("Please select an intensity level for deficit or surplus.", "error")
                return redirect(url_for('goals'))

            # Get user's TDEE from database
            tdee = found_user.tdee

            # Calculate calorie goal
            caloriesRequired, warning = calculateCalorieGoals(tdee, goal, intensity)
            if warning:
                flash(warning, "warning")

            # Update the database with the new values
            found_user.goal = goal
            found_user.intensity = intensity
            found_user.caloriesRequired = caloriesRequired
            db.session.commit()

            # Flash success message
            flash(f"Goal updated to {goal} with {intensity if intensity else 'no'} intensity.", "success")

    return render_template('goals.html')

# Activity page
@app.route('/activity')
def activity():
    return render_template('activity.html')

# Calories page
@app.route('/calories')
def calories():
    return render_template('calories.html')

# Account page
@app.route('/account', methods=['POST', 'GET'])
def account():
    # Get User session and their database username
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    # Get User session and their database username
    if request.method == 'POST':
        action = request.form.get('action')
        messages = []

        # Takes in POST requests (if user presses a button)
        if action == 'updateDetails':
            new_weight = request.form.get('getWeight')
            new_height = request.form.get('getHeight')
            new_age = request.form.get('getAge')
            new_gender = request.form.get('gender', 'male')
            new_exercise_level = request.form.get('exercise_level')
        
            weight_changed = False
            height_changed = False
            age_changed = False
            gender_changed = False
            exercise_changed = False
            bmr_changed = False

            # Only update if the value has actually changed
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
                messages.append(f"Exercise level updated to {found_user.exercise_level.replace("_", " ").title()}") 
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

            # Only flash messages if something actually changed
            if messages:
                flash(", ".join(messages), "success")

            # Commit changes to the database
            db.session.commit()
        
        # Handle Logout
        if action == 'logout':
            flash('You have been logged out!', 'success')
            session.pop('username', None)
            return redirect(url_for('login'))

        # Handle Delete Account
        if action == 'delete':
            db.session.delete(found_user)
            db.session.commit()
            session.pop('username', None)
            flash('Account deleted successfully!', 'success')
            return redirect(url_for('login'))


    return render_template(
        'account.html',
        username=username,
        user_db=found_user
    )

def import_nutrition_data(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row

        for row in reader:
            def safe_float(value):
                try:
                    return float(value) if value not in ['t', '', None] else 0.0
                except ValueError:
                    return None  # Handle any unexpected errors

            food_name = row[0]  # Food Name
            measure = row[1]  # Measure
            grams = safe_float(row[2])  # Grams
            calories = safe_float(row[3])  # Calories
            protein = safe_float(row[4])  # Protein
            fat = safe_float(row[5])  # Fat
            sat_fat = safe_float(row[6])  # Saturated Fat
            fiber = safe_float(row[7])  # Fiber
            carbs = safe_float(row[8])  # Carbohydrates
            category = row[9]  # Category

            # Check if the meal already exists
            existing_meal = Meal.query.filter_by(food_name=food_name).first()
            if not existing_meal:
                # Insert only if it does not exist
                meal = Meal(food_name, measure, grams, calories, protein, fat, sat_fat, fiber, carbs, category)
                db.session.add(meal)

        db.session.commit()
        print("Data imported successfully!")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import_nutrition_data('data/meals.csv')
    app.run(debug=True)
