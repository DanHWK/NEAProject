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
    db.init_app(app) #configuring the application to support the db
    db.drop_all()
    db.create_all()

    login_manager = LoginManager()
    login_manager.init_app(app)
    # creates an object of the LoginManage() class that allows the app and the flask_login module to work together

    @login_manager.user_loader
    def load_user(user_id):
        #user_id is the primary key of the user table
        return User.query.get(int(user_id))
        # returns the user object when given the user id

def getCalories(query):
    api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
    response = requests.get(api_url + query, headers={'X-Api-Key': 'CykZrnTm3hnrG+/WRu3gwA==soLKPt0ZajLEdfyi'})
    if response.status_code == requests.codes.ok:
        print(response.json())
        items = response.json().get('items')
        calories = 0
        for item in items:
            calories += item.get('calories')

        return calories
    else:
        print("Error:", response.status_code, response.text)

@app.route("/")
def home():
    if current_user.is_authenticated == True:
        #username = User.query.filter_by(name=name)
        return render_template("homepage.html", )
    else:
        username = "user"
        return render_template("homepage.html",username = username)

@app.route("/fitness", methods = ["POST","GET"])
@login_required
def fitness():
    if request.method == "POST":
        exercise_hours = request.form.get("exercise_hours")
        exercise_minutes = request.form.get("exercise_minutes")
        MET_value = request.form.get("MET_value")
        new_exercise_record = ExerciseRecord(hours = exercise_hours, minutes = exercise_minutes, stored_MET_value = MET_value, user_id=current_user.id)

        # push to database
        try:
            db.session.add(new_exercise_record)
            db.session.commit()

        except:
            return "There was an error whilst recording your activity"

        return redirect("/fitness")
    else:
        return render_template("fitness.html")

@app.route("/diet", methods = ["POST", "GET"])
@login_required
def diet():
    if request.method == "POST":
        calories = getCalories(request.form.get("meal_name"))
        meal_name = request.form.get("meal_name")
        meal_time = request.form.get("meal_time")
        new_meal_record = MealRecord(name = meal_name, time = meal_time, calories = calories, user_id=current_user.id)

        # push to database
        try:
            db.session.add(new_meal_record)
            db.session.commit()

        except:
            return "There was an error whilst recording your meal"

        return redirect("/diet")
    else:
        return render_template("diet.html")

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
