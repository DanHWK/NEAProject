import pygal
from datetime import datetime
import calendar

from flask import Flask
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import select
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord, User


class Graph:
    def __init__(self,timeframe):
        self.title = "title"
        self.timeframe = timeframe
        self.linename1 = "line1"
        y_axis_values = []
        global today
        today = datetime.utcnow()
        #Stores the current UTC time

        global weekday
        weekday = today.weekday()
        #Gets the current weekday

        global calendar_object
        calendar_object = calendar.Calendar()
        #Creates a calendar object

        global dates_in_month
        dates_in_month = calendar_object.itermonthdates(today.year,today.month)
        #Gets all the days in the month in this year in the form of datetime objects

    def get_y_axis_values():
        pass

    def get_x_axis_values(self):
        x_axis_values = []
        days_of_the_week = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

        if self.timeframe == "day":
            current_day = days_of_the_week[weekday]
            x_axis_values.append(current_day)
            return x_axis_values
            # returns the x axis values for a day graph

        elif self.timeframe == "week":
            x_axis_values = days_of_the_week
            return x_axis_values
            # returns the x axis values for a week graph

        elif self.timeframe == "month":
            for dates in dates_in_month:
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

    def create_graph(self):
        graph_data = pygal.Line()
        #Calls upon the line graph function of pygal
        graph_data.title = self.title
        #assigns the name of the graph

        graph_data.x_labels = map(str,self.get_x_axis_values())
        #Gets the x axis values

        graph_data.add(self.linename1, [5,4,2,5,6,8,9,10])
        #Creates the line with it's name and values

        return graph_data
        #Returns all the graph data where it will then be rendered in the app

class MealGraph(Graph):
    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Diet graph"
        self.linename1 = "Calories consumed"

        global currentuser
        currentuser = current_user.id

    def daily_calories_consumed(date):
        #user_meal_data = db.session.execute(select(MealRecord).where(MealRecord.user_id == current_user.id).order_by(MealRecord.date_created))
        date = date
        user_meal_data = MealRecord.query.filter_by(user_id = currentuser, date_created = date)
        print(user_meal_data)
        print(date)

    def get_y_axis_values():
        pass
