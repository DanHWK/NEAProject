import pygal
from datetime import datetime, timedelta
import calendar

from flask import Flask
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import select
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord, User, StreakRecord


class Graph:
    def __init__(self,timeframe):
        self.title = "title"
        self.timeframe = timeframe
        self.linename1 = "line1"
        self.linename2 = "line2"
        self.desired_goal = "desired goal"
        #All values here apart from timeframe are to be reassigned new values
        #They are just here to be used as a common interface for functions

        global today
        today = datetime.now()
        #Stores the current  time

        global weekday
        weekday = today.weekday()
        #Gets the current weekday

        global calendar_object
        calendar_object = calendar.Calendar()
        #Creates a calendar object

        global currentuser
        currentuser = current_user.id
        #stores the current user id in this variable

        global goals
        goals = GoalRecord.query.filter_by(user_id = currentuser).first()
        #stores the GoalRecord query of the current user in this variable, there should only be one Goal Record per user

    def calculate_daily_values(self, date):
        pass

    def get_y_axis_values(self):
        y_axis_values = []
        if self.timeframe == "day":
            y_axis_values.append(self.calculate_daily_values(datetime.now().strftime('%Y-%m-%d')))
            return y_axis_values

        elif self.timeframe == "week":
            for dates in calendar_object.itermonthdates(today.year,today.month):
                if datetime.now().strftime('%W') == dates.strftime('%W'):
                    y_axis_values.append(self.calculate_daily_values(dates.strftime('%Y-%m-%d')))
            return y_axis_values

        elif self.timeframe == "month":
            for dates in calendar_object.itermonthdates(today.year,today.month):
                if dates.month == today.month:
                    y_axis_values.append(self.calculate_daily_values(dates.strftime('%Y-%m-%d')))
            return y_axis_values

    def get_x_axis_values(self):
        x_axis_values = []
        days_of_the_week = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

        if self.timeframe == "day":
            current_day = days_of_the_week[weekday]
            x_axis_values.append(current_day)
            return x_axis_values
            # returns the x axis values for a day graph
            # this is done so if it is looking for day graph data it doesn't have to run through the other if statements

        elif self.timeframe == "week":
            x_axis_values = days_of_the_week
            return x_axis_values
            # returns the x axis values for a week graph

        elif self.timeframe == "month":
            for dates in calendar_object.itermonthdates(today.year,today.month):
            #Goes through all the dates in the month
                if dates.month == today.month:
                    #Itermonth dates also includes all the days before the start of the month
                    #and after the end of the month to get complete weeks
                    #The if statement above makes sure to only include dates that are
                    #actually in the current month
                    x_axis_values.append(dates.strftime("%d"))
                    #converts the datetime objects into strings and adds them to the x_axis_values list
                    #It will represent each day of the month as a decimal number
            return x_axis_values
            # returns the x axis values for a month graph

    def get_goal(self):
        goal_graph_data = []

        if self.timeframe == "day":
            goal_graph_data.append(self.desired_goal)
            return goal_graph_data

        elif self.timeframe == "week":
            for x in range(0,7):
            #This for loop makes it so every day in the week displays the goal value
            #This is so it doesn't just look like a single dot on the graph
                goal_graph_data.append(self.desired_goal)
            return goal_graph_data

        elif self.timeframe == "month":
            for x in range(0,31):
                goal_graph_data.append(self.desired_goal)
            return goal_graph_data

    def create_graph(self):
        graph_data = pygal.Line(include_x_axis=True)
        #Calls upon the line graph function of pygal
        graph_data.title = self.title
        #assigns the name of the graph

        graph_data.x_labels = map(str,self.get_x_axis_values())
        #Gets the x axis values

        graph_data.add(self.linename1, self.get_y_axis_values())
        #Creates the line with the values in the database

        graph_data.add(self.linename2, self.get_goal())
        #Line for goal value

        return graph_data
        #Returns all the graph data where it will then be rendered in the app

class MealGraph(Graph):
    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Diet graph"
        self.linename1 = "Calories consumed"
        self.linename2 = "Meal Goal calories"
        # Set the names of the lines and the title of the graph
        self.desired_goal = goals.meal_goal

    def calculate_daily_values(self, date):
        day_calories_consumed = 0
        user_meal_data = MealRecord.query.filter_by(user_id = currentuser, date_created = date).all()
        #Gets all the meal records created on the specified date
        for x in user_meal_data:
            day_calories_consumed = day_calories_consumed + x.calories
            #Add all the calories of the meal records for that day
        if user_meal_data != []:
            #if there is meal data return the total calories consumed for that day
            return day_calories_consumed
        else:
            return 0

class ExerciseGraph(Graph):

    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Fitness graph"
        self.linename1 = "Calories burnt"
        self.linename2 = "Exercise Goal calories"
        # Set the names of the lines and the title of the graph
        self.desired_goal = goals.exercise_goal

    def calculate_daily_values(self, date):
        day_calories_burnt = 0
        user_exercise_data = ExerciseRecord.query.filter_by(user_id = currentuser, date_created = date).all()
        #Gets all the exercise records created on the specified date
        for x in user_exercise_data:
            day_calories_burnt = day_calories_burnt + x.calories_burned
            #Add all the calories burnt from the exercise records for that day
        if user_exercise_data != []:
            #if there is exercise data return the total calories burnt from exercise for that day
            return day_calories_burnt
        else:
            return 0

class SleepGraph(Graph):

    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Sleep graph"
        self.linename1 = "Hours of sleep"
        self.linename2 = "Sleep goal hours"
        # Set the names of the lines and the title of the graph
        self.desired_goal = goals.sleep_goal

    def calculate_daily_values(self, date):
        day_sleep_hours = 0
        user_sleep_data = SleepRecord.query.filter_by(user_id = currentuser, date_created = date).all()
        #Gets all the Sleep records created on the specified date
        for x in user_sleep_data:
            day_sleep_hours = day_sleep_hours+ int(x.hours_slept) +(x.minutes_slept/60)
            #Add all the sleep hours for the specified day, minutes are converted into hours by divding by 60
        if user_sleep_data != []:
            #if there is sleep data return the total hours of sleep for that day
            return day_sleep_hours
        else:
            return 0

class WeightGraph(Graph):

    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Weight graph"
        self.linename1 = "Weight (kg)"
        self.linename2 = "Weight goal (kg)"
        # Set the names of the lines and the title of the graph
        self.desired_goal = goals.weight_goal

    def calculate_daily_values(self, date):
        day_weight = 0
        user_weight_data = WeightRecord.query.filter_by(user_id = currentuser, date_created = date).all()
        #Gets all the weight records created on the specified date
        weight_values = []
        number_of_weight_records = 0
        total_weight_value = 0

        for x in user_weight_data:
            weight_values.append(x.weight)
            number_of_weight_records = number_of_weight_records+1

        for x in weight_values:
            total_weight_value = total_weight_value+x
        #These for loops are used to get the value needed to calculate the average weight value of the day

        if user_weight_data != []:
            average_weight_value = total_weight_value/number_of_weight_records
            #if there is weight data return the average weight for the day
            return average_weight_value
        else:
            return 0
            #returns 0 instead of pass to prevent an error in the streak system
            #caused by the code trying to compare None to an integer