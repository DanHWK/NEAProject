from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
import requests
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord, User, StreakRecord
import bcrypt
import pygal
from datetime import datetime, timedelta
import calendar
from graphclasses import GraphManager
from streakclass import StreakManager
import re
import logging


app = Flask(__name__)
#Gets the app configured for the databases.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///record.db'
#Configures the app to the secret key and allows it to use sessions to store user information.
app.config['SECRET_KEY'] = b'3733939879b55267c99dee411ca3c0369437268c9781771dcd258859f270292a'

with app.app_context():
    db.init_app(app) #Configuring the application to support the db, needed because db is defined globally.
    db.drop_all()
    db.create_all()

    #Allows the app and the flask_login module to work together.
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    #Configure logging to log to a file with a specific format.
    logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s : %(message)s')

    @login_manager.user_loader
    def load_user(user_id):
        #user_id is the primary key of the user table.
        #Returns the user object's id as an integer when given the user id.
        return User.query.get(int(user_id))

def get_total_calories(query):
    '''
    Calculates the total number of calories in a meal using an external api.

    Parameters:
        query(str): The meal input by the user.

    Returns:
        int: The total number of calories.
    '''
    api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
    api_key = 'CykZrnTm3hnrG+/WRu3gwA==soLKPt0ZajLEdfyi'  #Required for authentication.
    response = requests.get(api_url + query, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        app.logger.info(f'Query: {query}, Response: {response.json()}')
        #Gets the items returned in the json response.
        items = response.json().get('items')
        calories = 0
        #Iterates through the items and sums up their calorie values.
        for item in items:
            calories += item.get('calories')

        return calories
    else:
        #Logs the error.
        app.logger.error(f'Status {response.status_code} - {response.text}')

def get_calories_burned(activity, duration_minutes, duration_hours):
    '''
    Calculates the total number of calories burned from an activity using an external api.

    Parameters:
        activity(str): The type of activity that has been done.
        duration_minutes(int): The number of minutes that the activity lasted for.
        duration_hours(int): The number of hours that the activity lasted for.

    Returns:
        int: The total number of calories burned.
    '''
    api_url = "https://trackapi.nutritionix.com/v2/natural/exercise"
    # The query needs to be formatted in a certain way.
    parameter = f'{activity} for {str(duration_minutes)} minutes and {str(duration_hours)} hours'
    # The API utilises AI to parse through the query and identify the correct number of calories burned.
    data = {"query":parameter}
    response = requests.post(api_url , headers = {"x-app-key":"cb4162e3761f026ca66e3e947f26ca3a" , "x-app-id": "4fc7ca2a"}, json = data)
    if response.status_code == requests.codes.ok:
        app.logger.info(f'Query: {data}, Response: {response.json()}')
        #Gets the exercises returned in the json response.
        exercises = response.json().get('exercises')

        calories_burned = 0
        #Iterates through the exercises and sums up their calorie values
        for exercise in exercises:
            calories_burned += exercise.get("nf_calories")
        return calories_burned
    else:
        #Logs the error.
        app.logger.error(f'Status {response.status_code} - {response.text}')

def test_password_strength(password):
    '''
    Determines whether the password input by the user matches the password requirements

    Parameters:
        password(str): The password input by the user.

    Returns:
        bool: Whether the password matches all the requirements or not.
        string: The reason the password failed the checks.
    '''
    #Regex patterns for the different password requirements.
    uppercase_letter_pattern = "(?=.*?[A-Z])"
    lowercase_letter_pattern = "(?=.*?[a-z])"
    digit_pattern = "(?=.*?[0-9])"
    special_character_pattern = "(?=.*?[#?!@$%^&*-])"

    #Checks whether the password input by the user matches the password requirements one by one
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.match(uppercase_letter_pattern, password):
        return False, "Password must contain at least one uppercase letter"
    if not re.match(lowercase_letter_pattern, password):
        return False, "Password must contain at least one lowercase letter"
    if not re.match(digit_pattern, password):
        return False, "Password must contain at least one digit"
    if not re.match(special_character_pattern, password):
        return False, "Password must contain at least one special character"

    return True, ""  #Means the password matches all the requirements it doesn't have a failure reason.

def validate_goal_input(input):
    '''
    Determines whether the goal value input by the user is valid

    Parameters:
        input(str): The goal value input by the user.

    Returns:
        bool: Whether the input is valid.
    '''
    #Goal value must be a valid number.
    try:
        if int(input) > 0:
            return True
        else:
            return False
    except:
        app.logger.error(f'An invalid goal was input by the user - {input}')
        return False

@app.route("/")
def home():
    #The user sees different things based on whether they are logged in or not.
    if current_user.is_authenticated == True:
        username = current_user.name
        #This boolean is passed to the HTML template and indicates what should be displayed to the user.
        user_logged_in = True

        graph_uris = GraphManager().graphs  #Gets the uris for all the graphs for the user.
        streak_manager = StreakManager()
        #Checks whether any of the streaks need to be reset and reset them if necessary.
        streak_manager.reset_streaks()
        #Gets the StreakRecord for the currently logged in user.
        Streak = StreakRecord.query.filter_by(user_id = current_user.id).first()
        return render_template("homepage.html", username = username, user_logged_in = user_logged_in, StreakRecord =  Streak, graph_uris = graph_uris)
    else:
        #If the user is not logged in only the "login" and "signup" buttons are shown.
        return render_template("homepage.html",username = "", user_logged_in = False)

@app.route("/fitness", methods = ["POST","GET"])
@login_required
def fitness():
    #Occurs if the user submits a form on the /fitness page on the website.
    if request.method == "POST":
        #Retrieves all the value input by the user.
        exercise_hours = request.form.get("exercise_hours")
        exercise_minutes = request.form.get("exercise_minutes")
        exercise_name = request.form.get("exercise_name")
        calories_burned = get_calories_burned(exercise_name, exercise_minutes, exercise_hours)   
        #Creates a new ExerciseRecord based on the values input by the user.
        new_exercise_record = ExerciseRecord(hours = exercise_hours, minutes = exercise_minutes, name = exercise_name, calories_burned = calories_burned, user_id=current_user.id,date_created = datetime.now().strftime('%Y-%m-%d'))
        #Tries to update the database with this new ExerciseRecord.
        try:
            db.session.add(new_exercise_record)
            db.session.commit()
        except:
            #Error handling if there is a problem with adding the record to the database
            app.logger.error(f'There was an error when trying to add {new_exercise_record} to the database')
            return "There was an error whilst recording your activity"
        #Checks whether the exercise streak needs to be increased and increases it if necessary.
        StreakManager().increase_streak(ExerciseRecord, calories_burned)
        #Renders the relevant html template.
        return render_template("fitness.html", success = True)
    else:
        return render_template("fitness.html")

@app.route("/diet", methods = ["POST", "GET"])
@login_required
def diet():
    #Occurs if the user submits a form on the /diet page on the website.
    if request.method == "POST":
        #If the user does not input the individual amount of of macronutrients in their meal
        #then calculate the amount of calories using the API. Otherwise calculate manually.
        if request.form.get("custom_meal_carbs") == None:
            calories = get_total_calories(request.form.get("meal_name"))
        else:
            #Calories calculated are based of the 4-9-4 system.
            # i.e 4 calories per gram of carbs, 9 calories per grams of fat and 4 calories per grams of protein.
            carbohydrates = int(request.form.get("custom_meal_carbs"))
            protein = int(request.form.get("custom_meal_protein"))
            fats = int(request.form.get("custom_meal_fats"))
            calories = (carbohydrates*4)+(protein*4)+(fats*9)

        #Means that the meal name input by the user is not recognised by the API as a food item
        if calories == 0:
            return render_template("diet.html", valid = False)
        #Retrieves all the value input by the user.
        meal_name = request.form.get("meal_name")
        meal_time = request.form.get("meal_time")
        #Creates a new MealRecord based on the values input by the user.
        new_meal_record = MealRecord(name = meal_name, time = meal_time, calories = calories, user_id=current_user.id, date_created = datetime.now().strftime('%Y-%m-%d'))
        #Tries to update the database with this new MealRecord.
        try:
            db.session.add(new_meal_record)
            db.session.commit()
        except:
            #Error handling if there is a problem with adding the record to the database
            app.logger.error(f'There was an error when trying to add {new_meal_record} to the database')
            return "There was an error whilst recording your meal"
        #Checks whether the meal streak needs to be increased and increases it if necessary.
        StreakManager().increase_streak(MealRecord, calories)
        #Renders the relevant html template
        return render_template("diet.html", success = True)
    else:
        return render_template("diet.html", success = False)

@app.route("/sleep", methods = ["POST", "GET"])
@login_required
def sleep():
    #Occurs if the user submits a form on the /sleep page on the website.
    if request.method == "POST":
        #Retrieves all the value input by the user.
        minutes_slept = request.form.get("minutes_slept")
        hours_slept = request.form.get("hours_slept")

        #Validates the user input
        if int(minutes_slept) < 0 or int(hours_slept) < 0 :
            return render_template("sleep.html", success = False, valid = False)
        else:
            #Creates a new SleepRecord based on the values input by the user.
            new_sleep_record = SleepRecord(minutes_slept = minutes_slept, hours_slept = hours_slept, user_id = current_user.id,date_created = datetime.now().strftime('%Y-%m-%d'))

        #Tries to update the database with this new SleepRecord.
        try:
            db.session.add(new_sleep_record)
            db.session.commit()
        except:
            #Error handling if there is a problem with adding the record to the database
            app.logger.error(f'There was an error when trying to add {new_sleep_record} to the database')
            return "There was an error whilst recording your activity"
        #How much sleep this newly added record would add to the daily total.
        increase_amount = int(hours_slept) + (int(minutes_slept)/60)
        #Checks whether the sleep streak needs to be increased and increases it if necessary.
        StreakManager().increase_streak(SleepRecord, increase_amount)
        #Renders the relevant html template.
        return render_template("sleep.html", success = True)
    else:
        return render_template("sleep.html", success = False)

@app.route("/weight", methods = ["POST", "GET"])
@login_required
def weight():
    #Occurs if the user submits a form on the /weight page on the website.
    if request.method == "POST":
        weight = request.form.get("weight")
        #Validates the user input
        if int(weight) < 0:
            return render_template("weight.html", success = False, valid = False)
        else:
            #Creates a new WeightRecord based on the value input by the user.
            new_weight_record = WeightRecord(weight = weight, user_id = current_user.id,date_created = datetime.now().strftime('%Y-%m-%d'))
        #Tries to update the database with this new WeightRecord.
        try:
            db.session.add(new_weight_record)
            db.session.commit()
        except:
            #Error handling if there is a problem with adding the record to the database
            app.logger.error(f'There was an error when trying to add {new_weight_record} to the database')
            return "There was an error whilst recording your activity"
        #Checks whether the sleep streak needs to be increased and increases it if necessary.
        StreakManager().increase_streak(WeightRecord)
        #Renders the relevant html template.
        return render_template("weight.html", success = True)
    else:
        return render_template("weight.html", success = False)

@app.route("/goals", methods = ["POST", "GET"])
@login_required
def goals():
    #Gets the GoalRecord for the currently logged in user.
    current_goals = GoalRecord.query.filter_by(user_id = current_user.id).first()
    #Occurs if the user submits a form on the /goal page on the website.
    if request.method == "POST":
        #Validates the user input.
        if request.form.get("new_meal_goal") != None:
            meal_goal = request.form.get("new_meal_goal")
            #Updates the relevant goal if valid.
            if(validate_goal_input(meal_goal)):
                current_goals.meal_goal = meal_goal
            else:
                return render_template('goals.html', current_goals = current_goals, valid = False)

        if request.form.get("new_exercise_goal") != None:
            exercise_goal = request.form.get("new_exercise_goal")
            #Updates the relevant goal if valid.
            if(validate_goal_input(exercise_goal)):
                current_goals.exercise_goal = exercise_goal
            else:
                return render_template('goals.html', current_goals = current_goals, valid = False)

        if request.form.get("new_sleep_goal") != None:
            sleep_goal = request.form.get("new_sleep_goal")
            #Updates the relevant goal if valid.
            if(validate_goal_input(sleep_goal)):
                current_goals.sleep_goal = sleep_goal
            else:
                return render_template('goals.html', current_goals = current_goals, valid = False)
        
        if request.form.get("new_weight_goal") != None:
            weight_goal = request.form.get("new_weight_goal")
            #Updates the relevant goal if valid.
            if(validate_goal_input(weight_goal)):
                current_goals.weight_goal = weight_goal
            else:
                return render_template('goals.html', current_goals = current_goals, valid = False)
        try:
            db.session.commit()
        except:
            #Error handling if there is a problem with adding the record to the database.
            app.logger.error(f'There was an error when trying to add {current_goals} to the database')
            return "There was an error whilst setting your new goals"
        return render_template("goals.html", current_goals = current_goals, success = True, valid = True)
    else:
        return render_template("goals.html", current_goals = current_goals, success = False)

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get('user_email')
        password = request.form.get('user_password')
        #Gets the user based on their email from the database.
        user = User.query.filter_by(email=email).first()

        #Checks that the user actually exists and that their password is correct.
        #Take the user-supplied password, hash it, and compare it to the hashed password in the database
        #The encoding of the input password must be changed to utf-8 due to the way it is stored in the database.
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page
        #If all the checks are passed then login the user
        login_user(user)
        return redirect(url_for('home'))
    else:
        return render_template("login.html")

@app.route("/signup", methods = ["POST", "GET"])
def signup():
    if request.method == "POST":
        email = request.form.get('user_email')
        name = request.form.get('user_name')
        #.encode('utf-8') turns the password data type from string to bytes which is needed to use the bcrypt salt function
        password = request.form.get('user_password').encode('utf-8')

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
        #Check whether the password input by the user passes all the requirements
        password_strength, password_failed_reason = test_password_strength(request.form.get('user_password'))

        if not password_strength:
            return render_template('signup.html', WeakPassword = True, password_failed_reason = password_failed_reason)

        if user: # if a user is found, we want to redirect back to signup page so user can try again as a email can only have one account
            #if a user isn't found the if statement will not run as user will equal None
            flash('Email address already exists')
            return redirect(url_for('signup'))
        
        #Generates a salt which is added to the password. This is done for security reasons as it means that when used
        #the same password will no longer yield the same hash, making the hash algorithm’s output unpredicatable.
        salt = bcrypt.gensalt()
        #Hash the password so the plaintext version isn't stored in the database.
        new_user = User(email=email, name=name, password=bcrypt.hashpw(password, salt))
        #Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        #Login the user in order to get the user id to create a GoalRecord
        login_user(new_user)
        #Sets default goals for the new user
        default_goal = GoalRecord(meal_goal = 2000, exercise_goal = 400, sleep_goal = 7, weight_goal = 70, user_id = current_user.id)
        #Create the streak record for the user which stores the values for the different type of streaks.
        default_streak = StreakRecord(user_id = current_user.id)
        #Add the StreakRecord and GoalRecord for the user to the database
        db.session.add(default_goal)
        db.session.add(default_streak)
        db.session.commit()
        #Log out the user and redirect to the login page so that the user inputs their login details to sign in.
        logout_user()
        return redirect(url_for('login'))
    else:
        return render_template("signup.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
    #Runs the app
