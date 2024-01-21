from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
import requests
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord, User
import bcrypt
import pygal
from datetime import datetime
import calendar
from graphclasses import Graph, MealGraph
#graphclasses are imported here to avoid the circular import problem
#This is because graphclasses imports app from app and thus can't be imported
#before the app is created


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///record.db'
#Gets the app configured for the databases

app.config['SECRET_KEY'] = b'3733939879b55267c99dee411ca3c0369437268c9781771dcd258859f270292a'
# Configures the app to the secret key and allows it to use sessions to store user information

with app.app_context():
    db.init_app(app) #configuring the application to support the db, needed because db is defined globally
    db.drop_all()
    db.create_all()

    login_manager = LoginManager()
    login_manager.init_app(app)
    # creates an object of the LoginManage() class that allows the app and the flask_login module to work together

    @login_manager.user_loader
    def load_user(user_id):
        #user_id is the primary key of the user table
        return User.query.get(int(user_id))
        # returns the user object's id as an integer when given the user id

def getCalories(query):
    #The query parameter will pass in the meal_name inputted by the user
    api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
    #This variable stores the URL of the external API
    response = requests.get(api_url + query, headers={'X-Api-Key': 'CykZrnTm3hnrG+/WRu3gwA==soLKPt0ZajLEdfyi'})
    #Sends a get request to CalorieNinjas along with the meal_name and the free API key that I was assigned for authentication
    if response.status_code == requests.codes.ok:
        #checks that there was no problem during transmission
        print(response.json())
        #prints the json file sent by CalorieNinjas in the terminal
        items = response.json().get('items')
        #retrieves all the items in json file
        calories = 0
        for item in items:
            calories += item.get('calories')
            #Seperates all the calorie values in the items and adds them up to find the total value

        return calories
        #returns the total calorie value
    else:
        print("Error:", response.status_code, response.text)
        #prints error message if there is a problem during transmission

def CaloriesBurned(activity, duration_minutes, duration_hours):
    api_url = "https://trackapi.nutritionix.com/v2/natural/exercise"
    parameter = activity+" for "+str(duration_minutes)+" minutes and "+str(duration_hours)+" hours"
    # The API accepts a string as a quety it then uses an AI to parse through the string to produce the calories burned
    data = {"query":parameter}
    response = requests.post(api_url , headers = {"x-app-key":"cb4162e3761f026ca66e3e947f26ca3a" , "x-app-id": "4fc7ca2a"}, json = data)
    if response.status_code == requests.codes.ok:
        print(parameter)
        print(response.json())

        exercises = response.json().get('exercises')
        #retrieves all the exercises in json file

        calories_burned = 0
        for exercise in exercises:
            calories_burned += exercise.get("nf_calories")
        return calories_burned
    else:
        print("Error:", response.status_code, response.text)

@app.route("/")
def home():
    if current_user.is_authenticated == True:
        #checks if the user has logged in, if the user has logged in the home page will display their username
        username = current_user.name
        user_logged_in = True
        #text that will only show when the user has logged in

        testgraph = Graph("month")
        graph_uri = testgraph.create_graph().render_data_uri()
        testmeal = MealGraph("month")
        testsql = MealGraph.daily_calories_consumed(datetime.utcnow().strftime('%Y-%m-%d'))

        return render_template("homepage.html", username = username, user_logged_in = user_logged_in, testgraphuri = graph_uri, testsql = testsql)
    else:
        #Passes these values to the homepage so nothing is shown when signing up
        return render_template("homepage.html",username = "", user_logged_in = False)

@app.route("/fitness", methods = ["POST","GET"])
@login_required
def fitness():
    if request.method == "POST":
        #If a form is sent from the website carry this code out
        exercise_hours = request.form.get("exercise_hours")
        exercise_minutes = request.form.get("exercise_minutes")
        exercise_name = request.form.get("exercise_name")
        calories_burned = CaloriesBurned(exercise_name, exercise_minutes, exercise_hours)
        #Retrieves all the value from the form
        new_exercise_record = ExerciseRecord(hours = exercise_hours, minutes = exercise_minutes, name = exercise_name, calories_burned = calories_burned, user_id=current_user.id)
        #Creates an object of the class ExerciseRecord and assigns all the values retrieved to attributes

        try:
            db.session.add(new_exercise_record)
            db.session.commit()
            # push to database
        except:
            return "There was an error whilst recording your activity"
            # Sends error message if there is a problem with adding the record to the database
        return render_template("fitness.html", success = True)
    else:
        return render_template("fitness.html")
        #Renders the html template fitness.html
@app.route("/diet", methods = ["POST", "GET"])
@login_required
def diet():
    if request.method == "POST":
        #If a form is sent from the website carry this code out
        if request.form.get("custom_meal_carbs") == None:
            calories = getCalories(request.form.get("meal_name"))
        else:
            carbohydrates = int(request.form.get("custom_meal_carbs"))
            protein = int(request.form.get("custom_meal_protein"))
            fats = int(request.form.get("custom_meal_fats"))
            #Calories calculated are based of the 4-9-4 system
            # i.e 4 calories per gram of carbs, 9 calories per grams of fat and 4 calories per grams of protein
            calories = (carbohydrates*4)+(protein*4)+(fats*9)

        #The if statement checks if a meal name is valid i.e recognised by calorieninjas as a food item
        if calories == 0:
            return render_template("diet.html", valid = False)
        meal_name = request.form.get("meal_name")
        meal_time = request.form.get("meal_time")
        #Retrieves all the value from the form
        new_meal_record = MealRecord(name = meal_name, time = meal_time, calories = calories, user_id=current_user.id)
        # push to database
        try:
            db.session.add(new_meal_record)
            db.session.commit()
        except:
            return "There was an error whilst recording your meal"
            # Sends error message if there is a problem with adding the record to the database
        return render_template("diet.html", success = True)
    else:

        return render_template("diet.html", success = False)

@app.route("/sleep", methods = ["POST", "GET"])
@login_required
def sleep():
    if request.method == "POST":
        minutes_slept = request.form.get("minutes_slept")
        hours_slept = request.form.get("hours_slept")

        new_sleep_record = SleepRecord(minutes_slept = minutes_slept, hours_slept = hours_slept, user_id = current_user.id)
        try:
            db.session.add(new_sleep_record)
            db.session.commit()
            # push to database
        except:
            return "There was an error whilst recording your activity"
                # Sends error message if there is a problem with adding the record to the database
        return render_template("sleep.html", success = True)
    else:
        return render_template("sleep.html", success = False)

@app.route("/weight", methods = ["POST", "GET"])
@login_required
def weight():
    if request.method == "POST":
        weight = request.form.get("weight")

        new_weight_record = WeightRecord(weight = weight, user_id = current_user.id)
        try:
            db.session.add(new_weight_record)
            db.session.commit()
            # push to database
        except:
            return "There was an error whilst recording your activity"
                # Sends error message if there is a problem with adding the record to the database
        return render_template("weight.html", success = True)
    else:
        return render_template("weight.html", success = False)

@app.route("/goals", methods = ["POST", "GET"])
@login_required
def goals():
    current_goals = GoalRecord.query.filter_by(user_id = current_user.id).first()
    if request.method == "POST":
        if request.form.get("new_meal_goal") != None:
            #Checks if the User filled in the input
            try:
            #Checks if the User gave a valid input
                int(request.form.get("new_meal_goal"))
                current_goals.meal_goal = request.form.get("new_meal_goal")
            except:
            #Renders the goal template with an error message if it isn't valid
                return render_template('goals.html', current_goals = current_goals, valid = False)

        if request.form.get("new_exercise_goal") != None:
            try:
                int(request.form.get("new_exercise_goal"))
                current_goals.exercise_goal = request.form.get("new_exercise_goal")
            except:
                return render_template('goals.html', current_goals = current_goals, valid = False)

        if request.form.get("new_sleep_goal") != None:
            try:
                int(request.form.get("new_sleep_goal"))
                current_goals.sleep_goal = request.form.get("new_sleep_goal")
            except:
                return render_template('goals.html', current_goals = current_goals, valid = False)

        if request.form.get("new_weight_goal") != None:
            try:
                int(request.form.get("new_weight_goal"))
                current_goals.weight_goal = request.form.get("new_weight_goal")
            except:
                return render_template('goals.html', current_goals = current_goals, valid = False)
        try:
            db.session.commit()
        except:
            return "There was an error whilst setting your new goals"
        current_goals = GoalRecord.query.filter_by(user_id = current_user.id).first()
        return render_template("goals.html", current_goals = current_goals, success = True, valid = True)
    else:
        return render_template("goals.html", current_goals = current_goals, success = False)

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get('user_email')
        password = request.form.get('user_password')

        user = User.query.filter_by(email=email).first()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password):
        #.encode('utf-8') turns the password data type from string to bytes, this is necessary as the password
        #is stored as the byte data type in the database.
            flash('Please check your login details and try again.')
            return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page

        login_user(user)
        return redirect(url_for('home'))
    else:
        return render_template("login.html")

@app.route("/signup", methods = ["POST", "GET"])
def signup():
    if request.method == "POST":
        email = request.form.get('user_email')
        name = request.form.get('user_name')
        password = request.form.get('user_password').encode('utf-8')
        #.encode('utf-8') turns the password data type from string to bytes, this is needed to use the bcrypt salt function
        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            #if a user isn't found the if statement will not run as user will equal None
            flash('Email address already exists')
            return redirect(url_for('signup'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.

        salt = bcrypt.gensalt() # Adding the salt to password
        #this is so if the same password is used they will have different hash values

        new_user = User(email=email, name=name, password=bcrypt.hashpw(password, salt))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        #logs in the user this is needed to get the user id for default_goal
        login_user(new_user)

        #set default goals for the new user
        default_goal = GoalRecord(meal_goal = 2000, exercise_goal = 2000, sleep_goal = 7, weight_goal = 70, user_id = current_user.id)
        #add the goal record to the database for the new user
        #this record will be edited if the user sets a new goal
        db.session.add(default_goal)
        db.session.commit()

        #succesful signup redirects to login page
        #logs out the user as it would cause an error when they try and use the log in page
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
