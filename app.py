from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("homepage.html")

@app.route("/fitness", methods = ["POST","GET"])
def fitness():
    exercise_hours = request.form.get("exercise_hours")
    exercise_minutes = request.form.get("exercise_minutes")
    MET_value = request.form.get("METvalue")
    return render_template("fitness.html")

@app.route("/diet", methods = ["POST", "GET"])
def diet():
    meal_name = request.form.get("meal_name")
    meal_time = request.form.get("meal_time")
    return render_template("diet.html")

if __name__ == "__main__":
    app.run(debug=True)
