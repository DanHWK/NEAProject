import logging
from flask import Flask
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import func
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord, User, StreakRecord

from datetime import datetime, timedelta
import calendar

from graphclasses import Graph, MealGraph, ExerciseGraph, SleepGraph, WeightGraph

class StreakManager():
    def __init__(self):
        self.streak_record = StreakRecord.query.filter_by(user_id = current_user.id).first()

    def set_streak(self, record_type, amount):
        if record_type == MealRecord:
            self.streak_record.meal_streak = amount
        elif record_type == ExerciseRecord:
            self.streak_record.exercise_streak = amount
        elif record_type == SleepRecord:
            self.streak_record.sleep_streak = amount
        elif record_type == WeightRecord:
            self.streak_record.weight_streak = amount

        db.session.commit()

    def get_current_streak(self, record_type):
        if record_type == MealRecord:
            return self.streak_record.meal_streak
        elif record_type == ExerciseRecord:
            return self.streak_record.exercise_streak
        elif record_type == SleepRecord:
            return self.streak_record.sleep_streak
        elif record_type == WeightRecord:
            return self.streak_record.weight_streak

    def get_recent_date(self, record_type):
        record = record_type.query.order_by((record_type.date_created).desc()).first()
        date_created = None if record is None else datetime.strptime(record.date_created, '%Y-%m-%d')
        return date_created

    def should_be_reset(self, latest_date):
        today = datetime.now()
        return latest_date < today

    def reset_streak(self, record_type):
        latest_date = self.get_recent_date(record_type)
        if latest_date == None or self.should_be_reset(latest_date):
            return

        self.set_streak(record_type, 0)

    def reset_streaks(self):
        self.reset_streak(MealRecord)
        self.reset_streak(ExerciseRecord)
        self.reset_streak(SleepRecord)
        self.reset_streak(WeightRecord)

    def get_goal(self, record_type):
        goal_record = GoalRecord.query.filter_by(user_id = current_user.id).first()

        if record_type == MealRecord:
            return goal_record.meal_goal
        elif record_type == ExerciseRecord:
            return goal_record.exercise_goal
        elif record_type == SleepRecord:
            return goal_record.sleep_goal

    def get_daily_value(self, record_type):
        today = datetime.now().strftime('%Y-%m-%d')
        if record_type == MealRecord:
            return MealGraph.calculate_daily_values(self, today)
        elif record_type == ExerciseRecord:
            return ExerciseGraph.calculate_daily_values(self, today)
        elif record_type == SleepRecord:
            return SleepGraph.calculate_daily_values(self, today)
        elif record_type == WeightRecord:
            return WeightGraph.calculate_daily_values(self, today)

    def has_streak_increased_today(self, record_type, increase_amount):
        if record_type == MealRecord:
            return self.get_daily_value(record_type) - increase_amount >= self.get_goal(record_type)
        elif record_type == ExerciseRecord:
            return self.get_daily_value(record_type) - increase_amount >= self.get_goal(record_type)
        elif record_type == SleepRecord:
            return self.get_daily_value(record_type) - increase_amount >= self.get_goal(record_type)

    def should_increase_streak(self, record_type, increase_amount):
        if record_type == WeightRecord:
            return db.session.query(func.count(WeightRecord.date_created == datetime.now().strftime('%Y-%m-%d'))).scalar() > 1
        if self.has_streak_increased_today(record_type, increase_amount):
            return False
        return self.get_daily_value(record_type) >= self.get_goal(record_type)

    def increase_streak(self, record_type, increase_amount = None):
        if not self.should_increase_streak(record_type, increase_amount):
            return

        self.set_streak(record_type, self.get_current_streak(record_type) + 1)