from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
import requests
from models import db, MealRecord, ExerciseRecord, User
import bcrypt

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

def CaloriesBurned(activity,duration):
    #api_url = 'https://api.api-ninjas.com/v1/caloriesburned'
    api_url = "https://trackapi.nutritionix.com/v2/natural/exercise?query="
    query = "swam for 1 hour"
    #query = {"activity":activity,"duration":str(duration)}
    # The query variable passes in the activity name and the duration
    # Duration needs to be converted from an integer into a string for the URL to work
    #response = requests.get(api_url, headers={'X-Api-Key': 'CykZrnTm3hnrG+/WRu3gwA==C6rJlO3bZqLjVfmP'}, params = query)
    response = requests.get(api_url + query, headers = {"x-app-key":"cb4162e3761f026ca66e3e947f26ca3a" , "x-app-id": "4fc7ca2a"}, )
    if response.status_code == requests.codes.ok:
        print(response.json())

    else:
        print("Error:", response.status_code, response.text)

@app.route("/")
def home():
    if current_user.is_authenticated == True:
        #checks if the user has logged in, if the user has logged in the home page will display their username
        username = current_user.name
        progress = "Progress"
        #text that will only show when the user has logged in
        return render_template("homepage.html", username = username, progress = progress)
    else:
        username = ""
        progress = ""
        return render_template("homepage.html",username = username, progress = progress)

@app.route("/fitness", methods = ["POST","GET"])
@login_required
def fitness():
    if request.method == "POST":
        #If a form is sent from the website carry this code out
        exercise_hours = request.form.get("exercise_hours")
        exercise_minutes = request.form.get("exercise_minutes")
        Intensity_value = request.form.get("Intensity_value")
        activity = "football"
        duration = (exercise_hours*60)+exercise_minutes
        calories = CaloriesBurned(activity,duration)
        #Retrieves all the value from the form
        new_exercise_record = ExerciseRecord(hours = exercise_hours, minutes = exercise_minutes, intensity = Intensity_value, user_id=current_user.id)
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
        calories = getCalories(request.form.get("meal_name"))
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

        #succesful signup redirects to login page
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
