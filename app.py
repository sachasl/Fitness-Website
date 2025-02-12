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

    def __init__(self, username):
        self.username = username
        self.weight = 90
        self.height = 1.75
        self.bmi = 0
        self.age = 48
        self.gender = 'male'
        
        
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
    username = session.get('username')
    found_user = User.query.filter_by(username=username).first()

    if not found_user:
        flash("User not found!", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')

        # List to store update messages
        messages = []

        if action == 'updateDetails':
            new_weight = request.form.get('getWeight')
            new_height = request.form.get('getHeight')
            new_age = request.form.get('getAge')
            new_gender = request.form.get('gender', 'male')

            # Update user details and add messages to list
            if new_weight:
                found_user.weight = float(new_weight)
                messages.append(f"Weight updated to {new_weight} kg")

            if new_height:
                found_user.height = float(new_height)
                messages.append(f"Height updated to {new_height} m")

            if new_age:
                found_user.age = int(new_age)
                messages.append(f"Age updated to {new_age} years")

            if new_gender and new_gender != found_user.gender:
                found_user.gender = new_gender
                messages.append(f"Gender updated to {new_gender}")

            # Update BMI if weight or height was changed
            if 'Weight' in messages or 'Height' in messages:
                found_user.bmi = calculateBMI(found_user.weight, 'kg', found_user.height, 'm')
                messages.append(f"BMI updated to {found_user.bmi}")

            # Flash all messages together
            if messages:
                flash(", ".join(messages), "success")

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

    return render_template('account.html', username=username, gender=found_user.gender)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

