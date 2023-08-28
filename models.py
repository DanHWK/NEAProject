from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy() #initialise database

#user table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(200))
    meals = db.relationship('MealRecord', backref='user')
    exercises = db.relationship('ExerciseRecord', backref='user')

#meal table
class MealRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    time = db.Column(db.String(50), nullable = False)
    calories = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

#exercise table
class ExerciseRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    hours = db.Column(db.Integer, nullable = False)
    minutes = db.Column(db.Integer, nullable = False)
    stored_MET_value = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
