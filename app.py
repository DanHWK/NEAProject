from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///record.db'
#initialise the database
db = SQLAlchemy(app)

#database model
class meal_record(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    time = db.Column(db.String(50), nullable = False)
    calories = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

#database model
class exercise_record(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    hours = db.Column(db.Integer, nullable = False)
    minutes = db.Column(db.Integer, nullable = False)
    stored_MET_value = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.drop_all()
    db.create_all()

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
    return render_template("homepage.html")

@app.route("/fitness", methods = ["POST","GET"])
def fitness():
    if request.method == "POST":
        exercise_hours = request.form.get("exercise_hours")
        exercise_minutes = request.form.get("exercise_minutes")
        MET_value = request.form.get("MET_value")
        new_exercise_record = exercise_record(hours = exercise_hours, minutes = exercise_minutes, stored_MET_value = MET_value)

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
def diet():
    if request.method == "POST":
        calories = getCalories(request.form.get("meal_name"))
        meal_name = request.form.get("meal_name")
        meal_time = request.form.get("meal_time")
        new_meal_record = meal_record(name = meal_name, time = meal_time, calories = calories)

        # push to database
        try:
            db.session.add(new_meal_record)
            db.session.commit()

        except:
            return "There was an error whilst recording your meal"

        return redirect("/diet")
    else:
        return render_template("diet.html")

if __name__ == "__main__":
    app.run(debug=True)
