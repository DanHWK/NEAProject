from flask_login import current_user
from sqlalchemy import func
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord, User, StreakRecord

from datetime import datetime, timedelta
from graphclasses import MealGraph, ExerciseGraph, SleepGraph, WeightGraph
from enum import Enum

import logging

class StreakType(Enum):
    DIET = 0
    SLEEP = 1
    EXERCISE = 2
    WEIGHT = 3

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
            record_type(StreakType): Indicates which streak type needs to be updated.
            amount(int): The number to set the streak to.
        '''
        match record_type:
            case StreakType.DIET:
                self.streak_record.meal_streak = amount
            case StreakType.EXERCISE:
                self.streak_record.exercise_streak = amount
            case StreakType.SLEEP:
                self.streak_record.sleep_streak = amount
            case StreakType.WEIGHT:
                self.streak_record.weight_streak = amount
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into set_streak()')
        
        db.session.commit() #Updates the database

    def get_current_streak(self, record_type):
        '''
        Gets the relevant streak value for a user from the database.

        Parameters:
            record_type(StreakType): Indicates which streak type needs to be retrieved.

        Returns:
            int: The revelant streak number.
        '''
        match record_type:
            case StreakType.DIET:
                return self.streak_record.meal_streak
            case StreakType.EXERCISE:
                return self.streak_record.exercise_streak
            case StreakType.SLEEP:
                return self.streak_record.sleep_streak
            case StreakType.WEIGHT:
                return self.streak_record.weight_streak
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into get_current_streak()')

    def get_recent_date(self, record_type):
        '''
        Gets the date of the most recently added record of a specific type from the database

        Parameters:
            record_type(db.Model): The type of record to check for.

        Returns:
            DateTime|None: The date of the most recently added record.
        '''
        #Order all the relevant records by the date_created column in descending order.
        #The first row would have the most recent date.
        record = record_type.query.filter_by(user_id = current_user.id).order_by((record_type.date_created).desc()).first()
        #If the query returns a record then return the date parsed as a DateTime object.
        date_created = None if record is None else datetime.strptime(record.date_created, '%Y-%m-%d')
        return date_created

    def has_date_been_skipped(self, latest_date):
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
    
    def was_streak_increased_yesterday(self, record_type):
        '''
        Determines whether the relevant streak was increased yesterday

        Parameters:
            record_type(StreakType): Indicates which record type this check applies to.
        Returns:
            bool: Whether the streak was increased yesterday
        '''
        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

        match record_type:
            case StreakType.DIET | StreakType.SLEEP | StreakType.EXERCISE:
                return self.get_daily_value(record_type, yesterday) >= self.get_goal(record_type)
            #The weight streak was increased if the user recorded their weight at least once. 
            case StreakType.Weight:
                record = WeightRecord.query.filter_by(user_id = current_user.id, date_created = yesterday).first()
                return False if record is None else True
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into was_streak_increased_yesterday()')
        
    def get_model(self, record_type):
        '''
        Gets the relevant database model for the streak type.

        Parameters:
            record_type(StreakType): Indicates which database model to retrieve .
        Returns:
            db.Model: The database model for the relevant type.
        '''
        match record_type:
            case StreakType.DIET:
                return MealRecord
            case StreakType.EXERCISE:
                return ExerciseRecord
            case StreakType.SLEEP:
                return SleepRecord
            case StreakType.WEIGHT:
                return WeightRecord
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into get_model()')

    def reset_streak(self, record_type):
        '''
        Determines whether a streak should be reset and reset it if necessary.

        Parameters:
            record_type(StreakType): Indicates which streak type needs to be checked.
        '''
        #The relevant database model needs to be retrieved in order to query the database correctly
        streak_db_model = self.get_model(record_type)
        latest_date = self.get_recent_date(streak_db_model)
        #If there are no records in the database for this record type then the streak doesn't need to be reset
        if latest_date == None:
            return
        
        #If there are records added within the appropriate timespan then we also have to check
        # whether the streak value was actually increased or not yesterday
        if not self.has_date_been_skipped(latest_date) and self.was_streak_increased_yesterday(record_type):
            return

        #Otherwise reset the streak to 0
        logging.info(f'Resetting the {record_type} streak to 0 for {current_user.name}')
        self.set_streak(record_type, 0)

    def reset_streaks(self):
        #Calls the method that resets the streak for each type of record
        for streak_type in StreakType:
            self.reset_streak(streak_type)
    
    def get_goal(self, record_type):
        '''
        Gets the goal of the relevant type from the database.

        Parameters:
            record_type(StreakType): Indicates which goal needs to be retrieved.
        Returns:
            int: The goal amount for the relevant type.
        '''
        #Queries the database for the GoalRecord that is linked to the currently logged in user
        goal_record = GoalRecord.query.filter_by(user_id = current_user.id).first()
        match record_type:
            case StreakType.DIET:
                return goal_record.meal_goal
            case StreakType.EXERCISE:
                return goal_record.exercise_goal
            case StreakType.SLEEP:
                return goal_record.sleep_goal
            case StreakType.WEIGHT:
                return goal_record.weight_goal
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into get_goal()')

    def get_daily_value(self, record_type, date):
        '''
        Gets the total value for the relevant record type for the day

        Parameters:
            record_type(StreakType): Indicates which record type the daily value need to be calculated for.
            date(str): The date for which to calculate the daily value for
        Returns:
            int: The total value amount for the relevant type for today.
        '''
        match record_type:
            case StreakType.DIET:
                return MealGraph.calculate_daily_values(self, date)
            case StreakType.EXERCISE:
                return ExerciseGraph.calculate_daily_values(self, date)
            case StreakType.SLEEP:
                return SleepGraph.calculate_daily_values(self, date)
            case StreakType.WEIGHT:
                return  WeightGraph.calculate_daily_values(self, date)
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into get_daily_goal()')

    def has_streak_increased_today(self, record_type, increase_amount):
        '''
        Determines whether the relevant streak has already been increased for today

        Parameters:
            record_type(StreakType): Indicates which record type this check applies to.
            increase_amount(int): The amount that the record that has just been added is increasing the daily value by
        Returns:
            bool: Whether the streak has already been increased today.
        '''
        #The weight record streak works differently which is why it isn't checked.

        #The check for whether a streak needs to be increased happens every time a new record is added.
        #So if the total value amount for today not including the most recently added record already reached
        #the goal, that means the streak was already increased when a different record was added today.
        match record_type:
            case StreakType.DIET | StreakType.SLEEP | StreakType.EXERCISE:
                today = datetime.now().strftime('%Y-%m-%d')
                return self.get_daily_value(record_type, today) - increase_amount >= self.get_goal(record_type)
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into has_streak_increased_today()')


    def should_increase_streak(self, record_type, increase_amount):
        '''
        Checks whether a streak should be increased or not

        Parameters:
            record_type(StreakType): Indicates which streak value this check applies to.

        Returns:
            boolean: Whether the streak should be increased.
        '''
        match record_type:
            #The weight record streak increases as long as the user has recorded their weight at least once for the day.
            case StreakType.WEIGHT:
                #Queries the database to get the amount of WeightRecords added today by the logged in user
                weight_record_count = db.session.query(func.count(
                    WeightRecord.date_created == datetime.now().strftime('%Y-%m-%d'), 
                    WeightRecord.user_id == current_user.id)).scalar()
                return weight_record_count >= 1
            case StreakType.DIET | StreakType.SLEEP | StreakType.EXERCISE:
                if self.has_streak_increased_today(record_type, increase_amount):
                    return False #A streak value should only be increased for each type once a day
                #Unless its for weight a streak should only be increased if the user has reached their goal for the day
                today = datetime.now().strftime('%Y-%m-%d')
                return self.get_daily_value(record_type, today) >= self.get_goal(record_type)
            case _:
                logging.error(f'Unknown StreakType {record_type} passed into should_increase_streak()')

    def increase_streak(self, record_type, increase_amount = None):
        '''
        Determines whether a streak should be increased and increase it if necessary.
        This is called every time a new record is added.

        Parameters:
            record_type(StreakType): Indicates which streak value this check applies to.
            increase_amount(int): The amount the newest record is increasing the daily value by.
            The weight streak doesn't depend on values which is why there is a default value of None.
        '''
        if not self.should_increase_streak(record_type, increase_amount):
            return
        #Only increase the streak if the checks pass
        logging.info(f'Increasing the {record_type} streak for {current_user.name}')
        self.set_streak(record_type, self.get_current_streak(record_type) + 1)