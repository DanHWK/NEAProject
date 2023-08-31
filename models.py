from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy() #initialise database

#meal table
class MealRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    time = db.Column(db.String(50), nullable = False)
    calories = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

#exercise table
class ExerciseRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    hours = db.Column(db.Integer, nullable = False)
    minutes = db.Column(db.Integer, nullable = False)
    stored_MET_value = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
