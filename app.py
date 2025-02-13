from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from modules import *

app = Flask(__name__)
# Encyption and lifetime for sessions
app.secret_key = 'secret'
app.permanent_session_lifetime = timedelta(days=5)
# Create database tables
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create database and its attributes
db = SQLAlchemy(app)

# Define User class for database
class User(db.Model):
    _id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(100))
    weight = db.Column('weight', db.Float, default=90)
    height = db.Column('height', db.Float, default=1.75)
    bmi = db.Column('bmi', db.Float)
    age = db.Column('age', db.Integer, default=48)
    gender = db.Column('gender', db.String(10), default='male')
    bmr = db.Column('bmr', db.Float)
    exercise_level = db.Column('exercise_level', db.String(20), default='sedentary')

    def __init__(self, username):
        self.username = username
        self.weight = 90
        self.height = 1.75
        self.bmi = calculateBMI(self.weight, self.height)
        self.age = 48
        self.gender = 'male'
        self.bmr = calculateBMR(self.weight, self.height, self.age, self.gender) 
        self.exercise_level = 'sedentary'
        
        
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
    # Displays hello 'username' on dashboard
    if 'username' in session:
        username = session['username']
        found_user = User.query.filter_by(username=username).first()
        return render_template('dashboard.html', username=username, user_db=found_user)
    else:
        return redirect(url_for('login')) 

# Meals page
@app.route('/meals')
def meals():
    return render_template('meals.html')

# Goals page
@app.route('/goals')
def goals():
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
                messages.append(f"Exercise level updated to {found_user.exercise_level}") 
                exercise_changed = True

            # Update BMI only if weight or height changed
            if weight_changed or height_changed:
                found_user.bmi = calculateBMI(found_user.weight, found_user.height)
                messages.append(f"BMI updated to {found_user.bmi}")

            # Update BMR only if weight, height, age, or gender changed
            if weight_changed or height_changed or age_changed or gender_changed:
                found_user.bmr = calculateBMR(found_user.weight, found_user.height, found_user.age, found_user.gender)
                messages.append(f"BMR updated to {found_user.bmr}")
                bmr_changed = True

            # Update TDEE only if BMR or exercise level changed
            if exercise_changed or bmr_changed:
                found_user.tdee = calculateTDEE(found_user.bmr, found_user.exercise_level)
                messages.append(f"TDEE updated to {found_user.tdee}")

            # Only flash messages if something actually changed
            if messages:
                flash(", ".join(messages), "success")

            db.session.commit()

    return render_template(
        'account.html',
        username=username,
        user_db=found_user
    )



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

