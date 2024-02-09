from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_login import UserMixin

db = SQLAlchemy() #This variable will be used to call upon SQLAlchemy() commands

#user table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(200))
    meals = db.relationship('MealRecord', backref='user')
    exercises = db.relationship('ExerciseRecord', backref='user')
    sleep = db.relationship('SleepRecord', backref='user')
    weight = db.relationship('WeightRecord', backref='user')
    goal = db.relationship('GoalRecord', backref='user')
    # Establishes a one to many relationship between the user database and the meal, sleep, weight, goal and exercise database.
    #establishes link to the ExerciseRecord table, User.exercises would refer to both the exercises record and user databases
    #backref = 'user' allows ExerciseRecord.user to also be used, basically turning it into a two way link

#meal table
class MealRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    time = db.Column(db.String(50), nullable = False)
    calories = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #The ForeignKey is linked to the primary key of the User database

#exercise table
class ExerciseRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    hours = db.Column(db.Integer, nullable = False)
    minutes = db.Column(db.Integer, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    calories_burned = db.Column(db.Integer)
    date_created = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #The ForeignKey is linked to the primary key of the User database

#sleep table
class SleepRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    hours_slept = db.Column(db.Integer, nullable = False)
    minutes_slept = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

#weight table
class WeightRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    weight = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

#goal table
class GoalRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    meal_goal = db.Column(db.Integer)
    exercise_goal = db.Column(db.Integer)
    sleep_goal = db.Column(db.Integer)
    weight_goal = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

#Streak table
class StreakRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    meal_streak = db.Column(db.Integer, default = 0)
    exercise_streak = db.Column(db.Integer, default = 0)
    sleep_streak = db.Column(db.Integer, default = 0)
    weight_streak = db.Column(db.Integer, default = 0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
