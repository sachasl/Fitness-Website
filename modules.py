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

# Calculate BMI
def calculateBMI(weight, unitW, height, unitH):
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
