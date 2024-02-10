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
    '''
    A class to manage all of the streaks for a user.

    Attributes:
        streak_record(StreakRecord): The StreakRecord in the database that is linked to the currently logged in user.
    '''
    def __init__(self):
        self.streak_record = StreakRecord.query.filter_by(user_id = current_user.id).first()

    def set_streak(self, record_type, amount):
        '''
        Updates the relevant streak value in the StreakRecord for a user in the database.

        Parameters:
            record_type(db.Model): Indicates which streak type needs to be updated.
            amount(int): The number to set the streak to.
        '''
        if record_type == MealRecord:
            self.streak_record.meal_streak = amount
        elif record_type == ExerciseRecord:
            self.streak_record.exercise_streak = amount
        elif record_type == SleepRecord:
            self.streak_record.sleep_streak = amount
        elif record_type == WeightRecord:
            self.streak_record.weight_streak = amount

        db.session.commit() #Updates the database

    def get_current_streak(self, record_type):
        '''
        Gets the relevant streak value for a user from the database.

        Parameters:
            record_type(db.Model): Indicates which streak type needs to be retrieved.

        Returns:
            int: The revelant streak number.
        '''
        if record_type == MealRecord:
            return self.streak_record.meal_streak
        elif record_type == ExerciseRecord:
            return self.streak_record.exercise_streak
        elif record_type == SleepRecord:
            return self.streak_record.sleep_streak
        elif record_type == WeightRecord:
            return self.streak_record.weight_streak

    def get_recent_date(self, record_type):
        '''
        Gets the date of the most recently added record of a specific type from the database

        Parameters:
            record_type(db.Model): The type of record to check for.

        Returns:
            DateTime or None: The date of the most recently added record.
        '''
        #Order all the relevant records by the date_created column in descending order.
        #The first row would have the most recent date.
        record = record_type.query.order_by((record_type.date_created).desc()).first()
        #If the query returns a record then return the date parsed as a DateTime object.
        date_created = None if record is None else datetime.strptime(record.date_created, '%Y-%m-%d')
        return date_created

    def should_be_reset(self, latest_date):
        '''
        Checks whether a streak should be reset according to the date of the latest record.

        Parameters:
            latest_date(DateTime): The date of the latest record in the database.

        Returns:
            boolean: Whether the streak should be reset.
        '''
        yesterday = (datetime.now() - timedelta(1))
        #If there is at least a one day gap in between today's date and the date of the
        #latest record then the streak should be reset
        return latest_date.date() < yesterday.date()

    def reset_streak(self, record_type):
        '''
        Determines whether a streak should be reset and reset it if necessary.

        Parameters:
            record_type(db.Model): Indicates which streak type needs to be checked.
        '''
        latest_date = self.get_recent_date(record_type)
        #If there are no records in the database for this record type or the check returns false
        #then the streak doesn't need to be reset
        if latest_date == None or not self.should_be_reset(latest_date):
            return
        #Otherwise reset the streak to 0
        self.set_streak(record_type, 0)

    def reset_streaks(self):
        #Calls the method that resets the streak is necessary for each type of record
        self.reset_streak(MealRecord)
        self.reset_streak(ExerciseRecord)
        self.reset_streak(SleepRecord)
        self.reset_streak(WeightRecord)

    def get_goal(self, record_type):
        '''
        Gets the goal of the relevant type from the database.

        Parameters:
            record_type(db.Model): Indicates which goal needs to be retrieved.
        Returns:
            int: The goal amount for the relevant type.
        '''
        #Queries the database for the GoalRecord that is linked to the currently logged in user
        goal_record = GoalRecord.query.filter_by(user_id = current_user.id).first()

        if record_type == MealRecord:
            return goal_record.meal_goal
        elif record_type == ExerciseRecord:
            return goal_record.exercise_goal
        elif record_type == SleepRecord:
            return goal_record.sleep_goal

    def get_daily_value(self, record_type):
        '''
        Gets the total value for the relevant record type for today

        Parameters:
            record_type(db.Model): Indicates which record type the daily value need to be calculated for.
        Returns:
            int: The total value amount for the relevant type for today.
        '''
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
        '''
        Determines whether the relevant streak has already been increased for today

        Parameters:
            record_type(db.Model): Indicates which record type this check applies to.
            increase_amount(int): The amount that the record that has just been added is increasing the daily value by
        Returns:
            bool: Whether the streak has already been increased today.
        '''
        #The weight record streak works differently which is why it isn't checked.

        #The check for whether a streak needs to be increased happens every time a new record is added.
        #So if the total value amount for today not including the most recently added record already reached
        #the goal, that means the streak was already increased when a different record was added today.
        if record_type == MealRecord:
            return self.get_daily_value(record_type) - increase_amount >= self.get_goal(record_type)
        elif record_type == ExerciseRecord:
            return self.get_daily_value(record_type) - increase_amount >= self.get_goal(record_type)
        elif record_type == SleepRecord:
            return self.get_daily_value(record_type) - increase_amount >= self.get_goal(record_type)

    def should_increase_streak(self, record_type, increase_amount):
        '''
        Checks whether a streak should be increased or not

        Parameters:
            record_type(db.Model): Indicates which streak value this check applies to.

        Returns:
            boolean: Whether the streak should be increased.
        '''
        #The weight record streak increases as long as the user has recorded their weight at least once for the day.
        if record_type == WeightRecord:
            #Queries the database to get the amount of WeightRecords added today
            weight_record_count = db.session.query(func.count(WeightRecord.date_created == datetime.now().strftime('%Y-%m-%d'))).scalar()
            return weight_record_count > 1
        if self.has_streak_increased_today(record_type, increase_amount):
            return False #A streak value should only be increased for each type once a day
        #Unless its for weight a streak should only be increased if the user has reached their goal for the day
        return self.get_daily_value(record_type) >= self.get_goal(record_type)

    def increase_streak(self, record_type, increase_amount = None):
        '''
        Determines whether a streak should be increased and increase it if necessary.
        This is called every time a new record is added.

        Parameters:
            record_type(db.Model): Indicates which streak value this check applies to.
            increase_amount(int): The amount the newest record is increasing the daily value by.
            The weight streak doesn't depend on values which is why there is a default value of None.
        '''
        if not self.should_increase_streak(record_type, increase_amount):
            return
        #Only increase the streak if the checks pass
        self.set_streak(record_type, self.get_current_streak(record_type) + 1)