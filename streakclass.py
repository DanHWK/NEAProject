from flask import Flask
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import select
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord, User, StreakRecord

from datetime import datetime, timedelta
import calendar

from graphclasses import Graph, MealGraph, ExerciseGraph, SleepGraph, WeightGraph

class Streak:
    def __init__(self):
        #These attributes will be assigned their proper values in the subclasses
        self.desired_streak = "desired streak value"
        self.latest_date_for_streak = "latest date for streak"
        #The latest date for a streak to continue on, after this date the streak is set back to 0
        self.streak_condition = "condition for streak value to be added"
        #The condition for the streak to continue
        self.streak_done = "stores whether a streak value has been added"
        #Boolean value is stored here to make sure only one streak value is added per day
        self.desired_goal = "desired goal"
        #The desired goal is stored here

        global currentuser
        currentuser = current_user.id

        global goals
        goals = GoalRecord.query.filter_by(user_id = currentuser).first()

        global StreakRecord
        StreakRecord = StreakRecord.query.filter_by(user_id = currentuser).first()

    def commit_streak_to_database():
        pass

    def create_streak(self):
        if self.streak_done == False:
            if self.latest_date_for_streak < datetime.now().strftime('%Y-%m-%d'):
                self.desired_streak = 0
                self.latest_date_for_streak = (datetime.now()+timedelta(days = 1)).strftime('%Y-%m-%d')
                self.commit_streak_to_database()
                # This function is used to commit the new streak record values to the database
                self.create_streak()
                # This if statement checks if its been more than one day since a value was added to the streak
                # If it has been more than one day the streak is set back to 0 and the latest date for a streak
                # to continue is increased by one, (if it didn't increase it the next if statement condition would never be fufilled)
                # The function is then called again to check if the user has met the conditions to start a new streak

            elif self.latest_date_for_streak >= datetime.now().strftime('%Y-%m-%d') and self.streak_condition > self.desired_goal:
                self.desired_streak = self.desired_streak + 1
                self.latest_date_for_streak = (datetime.now()+timedelta(days = 1)).strftime('%Y-%m-%d')
                self.streak_done = True
                self.commit_streak_to_database()
                pass
            pass
            #this pass is for when there is still time to continue the streak but the condition hasn't been fufilled

        elif self.streak_done == True:
            if datetime.now().strftime('%Y-%m-%d') >= self.latest_date_for_streak:
                self.streak_done = False
                self.commit_streak_to_database()
                self.create_streak()
                # This if statement checks if its been more than a day since the last streak value was added
                # >= is used as latest_date_for_streak is equal to the date when the last streak value was added plus one day
                # The function then calls upon itself to check if a streak value should be added again

            else:
                pass

class MealStreak(Streak):
    def __init__(self):
        Streak.__init__(self)
        self.desired_streak = StreakRecord.meal_streak
        self.latest_date_for_streak = StreakRecord.latest_date_for_meal_streak
        self.streak_condition = MealGraph.calculate_daily_values(datetime.now().strftime('%Y-%m-%d'))
        self.streak_done = StreakRecord.meal_streak_done
        self.desired_goal = goals.meal_goal

    def commit_streak_to_database(self):
        StreakRecord.meal_streak = self.desired_streak
        StreakRecord.meal_streak_done = self.streak_done
        StreakRecord.latest_date_for_meal_streak = self.latest_date_for_streak
        db.session.commit()
        pass
        # This function is used to commit the new streak record values to the database

class ExerciseStreak(Streak):
    def __init__(self):
        Streak.__init__(self)
        self.desired_streak = StreakRecord.exercise_streak
        self.latest_date_for_streak = StreakRecord.latest_date_for_exercise_streak
        self.streak_condition = ExerciseGraph.calculate_daily_values(datetime.now().strftime('%Y-%m-%d'))
        self.streak_done = StreakRecord.exercise_streak_done
        self.desired_goal = goals.exercise_goal

    def commit_streak_to_database(self):
        StreakRecord.exercise_streak = self.desired_streak
        StreakRecord.exercise_streak_done = self.streak_done
        StreakRecord.latest_date_for_exercise_streak = self.latest_date_for_streak
        db.session.commit()
        pass

class SleepStreak(Streak):
    def __init__(self):
        Streak.__init__(self)
        self.desired_streak = StreakRecord.sleep_streak
        self.latest_date_for_streak = StreakRecord.latest_date_for_sleep_streak
        self.streak_condition = SleepGraph.calculate_daily_values(datetime.now().strftime('%Y-%m-%d'))
        self.streak_done = StreakRecord.sleep_streak_done
        self.desired_goal = goals.sleep_goal

    def commit_streak_to_database(self):
        StreakRecord.sleep_streak = self.desired_streak
        StreakRecord.sleep_streak_done = self.streak_done
        StreakRecord.latest_date_for_sleep_streak = self.latest_date_for_streak
        db.session.commit()
        pass

class WeightStreak(Streak):
        def __init__(self):
            Streak.__init__(self)
            self.desired_streak = StreakRecord.weight_streak
            self.latest_date_for_streak = StreakRecord.latest_date_for_weight_streak
            self.streak_condition = WeightGraph.calculate_daily_values(datetime.now().strftime('%Y-%m-%d'))
            self.streak_done = StreakRecord.weight_streak_done
            self.desired_goal = goals.weight_goal

        def commit_streak_to_database(self):
            StreakRecord.weight_streak = self.desired_streak
            StreakRecord.weight_streak_done = self.streak_done
            StreakRecord.latest_date_for_weight_streak = self.latest_date_for_streak
            db.session.commit()
            pass

        def create_streak(self):
            #The if statement with the streak condition is changed here here so the streak value will increase as long as the user records
            #Their weight at least once a day
            if self.streak_done == False:
                if self.latest_date_for_streak < datetime.now().strftime('%Y-%m-%d'):
                    self.desired_streak = 0
                    self.latest_date_for_streak = (datetime.now()+timedelta(days = 1)).strftime('%Y-%m-%d')
                    self.commit_streak_to_database()
                    # This function is used to commit the new streak record values to the database
                    self.create_streak()
                    # This if statement checks if its been more than one day since a value was added to the streak
                    # If it has been more than one day the streak is set back to 0 and the latest date for a streak
                    # to continue is increased by one, (if it didn't increase it the next if statement condition would never be fufilled)
                    # The function is then called again to check if the user has met the conditions to start a new streak

                elif self.latest_date_for_streak >= datetime.now().strftime('%Y-%m-%d') and self.streak_condition != 0:
                    self.desired_streak = self.desired_streak + 1
                    self.latest_date_for_streak = (datetime.now()+timedelta(days = 1)).strftime('%Y-%m-%d')
                    self.streak_done = True
                    self.commit_streak_to_database()
                    pass
                pass
                #this pass is for when there is still time to continue the streak but the condition hasn't been fufilled

            elif self.streak_done == True:
                if datetime.now().strftime('%Y-%m-%d') >= self.latest_date_for_streak:
                    self.streak_done = False
                    self.commit_streak_to_database()
                    self.create_streak()
                    # This if statement checks if its been more than a day since the last streak value was added
                    # >= is used as latest_date_for_streak is equal to the date when the last streak value was added plus one day
                    # The function then calls upon itself to check if a streak value should be added again

                else:
                    pass
