# convert height from feet and inches to metres
def intoMetres(feet, inches):
    metres = feet * 0.3048
    metres += inches * 0.0254
    return round(metres, 2)


# convert height from metres to feet and inches
def toFeetInches(metres):
    totalFeet = metres * 3.28084
    feet = int(totalFeet)
    inches = round((totalFeet - feet) * 12)

    if inches == 12:
        feet += 1
        inches = 0
    return feet, inches


# convert weight from kg to lbs and vice versa
def convertWeight(weight, unit):
    if unit == 'kg':
        weight *= 2.2046
    if unit == 'lbs':
        weight /= 2.20406
    return round(weight, 2)

# Calculate user BMI
def calculateBMI(weight, height, unitW='kg', unitH='m'):
    if unitW == 'lbs':
        weight = convertWeight(weight, 'lbs')
    if unitH == 'ft':
        height = intoMetres(height[0], height[1])
    bmi = weight / (height ** 2)
    return round(bmi, 2)

# Calculate base metabolic rate
def calculateBMR(weight, height, age, gender, unitH='m', unitW='kg'):
    if unitW == 'lbs':
        weight = convertWeight(weight, 'lbs')
    if unitH == 'ft':
        height = intoMetres(height[0], height[1])
    height *= 100
    if gender == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    elif gender == 'female':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    return round(bmr, 2)

# Calculate Total Daily Energy Expenditure
def calculateTDEE(bmr, exericise_level):
    if exericise_level == 'sedentary':
        bmr *= 1.2
    elif exericise_level == 'lightly_active':
        bmr *= 1.375
    elif exericise_level == 'moderately_active':
        bmr *= 1.55
    elif exericise_level == 'very_active':
        bmr *= 1.725
    elif exericise_level == 'super_active':
        bmr *= 1.9
    return round(bmr, 2)

# Calculate Calories Required with Calorie Deficit
def CalorieDeficit(tdee, deficit):
    warning = None
    if deficit == 'mild':
        caloriesRequired = tdee - 200
    elif deficit == 'moderate':
        caloriesRequired = tdee - 300
    elif deficit == 'extreme':
        caloriesRequired = tdee - 500
        warning = 'This is an extreme calorie deficit. Use with caution'
    return round(caloriesRequired), warning

# Calculate Calories Required with Calorie Surplus
def calorieSurplus(tdee, surplus):
    warning = None
    if surplus == 'mild':
        caloriesRequired = tdee * 1.05
    elif surplus == 'moderate':
        caloriesRequired = tdee * 1.10
    elif surplus == 'extreme':
        caloriesRequired = tdee * 1.15
        warning = 'This is an extreme calorie surplus. Use with caution'
    return round(caloriesRequired), warning

# Calculate the users calorie goals
def calculateCalorieGoals(tdee, goal, intensity):
    warning = None
    if goal == 'maintain':
        caloriesRequired = tdee
    elif goal == 'deficit':
        caloriesRequired, warning = CalorieDeficit(tdee, intensity)
    elif goal == 'surplus':
        caloriesRequired, warning = calorieSurplus(tdee, intensity)
    return round(caloriesRequired), warning

# Checks if the user has met their macro goals and returns a message if they have.
def check_goal_achievement(user):
    messages = []
    # Margin for goal completion
    calorie_margin = 30
    macro_margin = 5

    if abs(user.caloriesRemaining) <= calorie_margin:
        messages.append("🎉 You've reached your calorie goal for today!")
    if abs(user.proteinRemaining) <= macro_margin:
        messages.append("💪 Great job! You've hit your protein goal!")
    if abs(user.fatRemaining) <= macro_margin:
        messages.append("🥑 Awesome! You've met your fat intake goal!")
    if abs(user.carbRemaining) <= macro_margin:
        messages.append("🍞 Congrats! You've hit your carb goal!")
    return messages

# Check if user has set up their account details
def user_details_complete(user):
    return all([
        user.weight is not None,
        user.height is not None,
        user.age is not None,
        user.gender is not None,
        user.exercise_level is not None,
        user.caloriesRequired is not None,
        user.proteinRequired is not None,
        user.fatRequired is not None,
        user.carbRequired is not None
    ])

# Function that is used to import data from the csv (only used once)
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
