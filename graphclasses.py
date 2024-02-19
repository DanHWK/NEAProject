import pygal
from datetime import datetime
import calendar
from flask_login import current_user
from models import db, MealRecord, ExerciseRecord, SleepRecord, WeightRecord, GoalRecord
import logging
from sqlalchemy import func

class Graph:
    '''
    A class used to represent a graph object.
    Acts as a common interface for the different graph types.

    Attributes:
        title(str): The graph's title
        timeframe(str): The timeframe that the graph should display
        linename1(str): The label for one of the lines on the graph
        linename2(str): The label for one of the other lines on the graph
        desiredgoal(str): The goal amount for the record type associated with the graph
    '''
    def __init__(self,timeframe):
        #All values here apart from timeframe are to be reassigned new values
        #They are just here to be used as a common interface for functions
        self.title = "title"
        self.timeframe = timeframe
        self.linename1 = "line1"
        self.linename2 = "line2"
        self.desired_goal = "desired goal"

        #Stores the current time.
        global today
        today = datetime.now()

        #Stores an integer representing what day of the week it is.
        global weekday
        weekday = today.weekday()

        #Creates a calendar object.
        global calendar_object
        calendar_object = calendar.Calendar()

        #Stores the id of the user currently logged in.
        global currentuser
        currentuser = current_user.id

        #The GoalRecord associated with the currently logged in user.
        global goals
        goals = GoalRecord.query.filter_by(user_id = currentuser).first()

    def calculate_daily_values(self, date):
        #Will be implemented by the child classes
        pass

    def get_y_axis_values(self):
        '''
        Gets the values for the graph's y-axis

        Returns:
            list: All the y-axis values
        '''
        y_axis_values = []
        match self.timeframe:
            case "day":
                #Just needs to get the values for today.
                y_axis_values.append(self.calculate_daily_values(datetime.now().strftime('%Y-%m-%d')))
                return y_axis_values
            case "week":
                for dates in calendar_object.itermonthdates(today.year,today.month):
                    #Gets all the dates for the current week and gets their corresponding values.
                    if datetime.now().strftime('%W') == dates.strftime('%W'):
                        y_axis_values.append(self.calculate_daily_values(dates.strftime('%Y-%m-%d')))
                return y_axis_values
            case "month":
                for dates in calendar_object.itermonthdates(today.year,today.month):
                    #Gets all the dates for the current month and gets their corresponding values.
                    if dates.month == today.month:
                        y_axis_values.append(self.calculate_daily_values(dates.strftime('%Y-%m-%d')))
                return y_axis_values
            case _:
                logging.error(f'Unknown graph timeframe {self.timeframe} was set - unable to get y-axis values')

    def get_x_axis_values(self):
        '''
        Gets the values for the graph's x-axis

        Returns:
            list: All the x-axis values
        '''
        x_axis_values = []
        days_of_the_week = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

        match self.timeframe:
            case "day":
                #Returns today's day
                current_day = days_of_the_week[weekday]
                x_axis_values.append(current_day)
                return x_axis_values
            case "week":
                #Returns all the days in a week
                x_axis_values = days_of_the_week
                return x_axis_values
            case "month":
                #Goes through all the dates in the month
                for dates in calendar_object.itermonthdates(today.year,today.month):
                    #Itermonth dates also includes all the days before the start of the month
                    #and after the end of the month to get complete weeks.
                    #This check ensures that only dates in the current month are included.
                    if dates.month == today.month:
                        #Adds each day in the month as a number
                        x_axis_values.append(dates.strftime("%d"))
                return x_axis_values
            case _:
                logging.error(f'Unknown graph timeframe {self.timeframe} was set - unable to get x-axis values')

    def create_graph(self):
        '''
        Creates a graph with the relevant values to be rendered

        Returns:
            A pygal object representing a line graph
        '''
        #Uses pygal to create a line graph
        graph_data = pygal.Line(include_x_axis=True)
        #Assigns the name of the graph
        graph_data.title = self.title
        #Gets and sets the x axis values for the graph
        x_axis_values = self.get_x_axis_values()
        graph_data.x_labels = map(str, x_axis_values)

        #Adds a line to the graph that represents the values that have been recorded by the user
        graph_data.add(self.linename1, self.get_y_axis_values())
        #Adds a horizontal line to the graph that indicates the user's goal
        graph_data.add(self.linename2, [self.desired_goal] * len(x_axis_values))

        return graph_data

class MealGraph(Graph):
    '''
    A class used to represent a graph that displays the user's meal data
    '''
    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Diet graph"
        self.linename1 = "Calories consumed"
        self.linename2 = "Meal Goal calories"
        self.desired_goal = goals.meal_goal

    def calculate_daily_values(self, date):
        '''
        Calculates the total value for all the meal records in a day for a user

        Parameters:
            date(str): Indicates the day that the total value need to be calculated for.
        Returns:
            int: The total value amount according to the user's meal records for a date
        '''
        #day_calories_consumed = 0
        #Gets all the meal records created on the specified date
        #user_meal_data = MealRecord.query.filter_by(user_id = currentuser, date_created = date).all()
        #Iterates through the meal records and sums up their calorie values
        #for x in user_meal_data:
            #day_calories_consumed = day_calories_consumed + x.calories

        day_calories_consumed = db.session.query(func.sum(MealRecord.calories)).group_by(MealRecord.user_id, MealRecord.date_created).having(MealRecord.user_id == currentuser,MealRecord.date_created == date).scalar()

        if day_calories_consumed == None:
            return 0

        return day_calories_consumed

class ExerciseGraph(Graph):
    '''
    A class used to represent a graph that displays the user's exercise data
    '''
    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Fitness graph"
        self.linename1 = "Calories burnt"
        self.linename2 = "Exercise Goal calories"
        self.desired_goal = goals.exercise_goal

    def calculate_daily_values(self, date):
        '''
        Calculates the total value for all the exercise records in a day for a user

        Parameters:
            date(str): Indicates the day that the total value need to be calculated for.
        Returns:
            int: The total value amount according to the user's exercise records for a date
        '''
        day_calories_burnt = db.session.query(func.sum(ExerciseRecord.calories_burned)).group_by(ExerciseRecord.user_id, ExerciseRecord.date_created).having(ExerciseRecord.user_id == currentuser,ExerciseRecord.date_created == date).scalar()

        if day_calories_burnt == None:
            return 0

        return day_calories_burnt

class SleepGraph(Graph):
    '''
    A class used to represent a graph that displays the user's sleep data
    '''
    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Sleep graph"
        self.linename1 = "Hours of sleep"
        self.linename2 = "Sleep goal hours"
        self.desired_goal = goals.sleep_goal

    def calculate_daily_values(self, date):
        '''
        Calculates the total value for all the sleep records in a day for a user

        Parameters:
            date(str): Indicates the day that the total value need to be calculated for.
        Returns:
            int: The total value amount according to the user's sleep records for a date
        '''
        day_sleep_hours = 0
        #Gets all the Sleep records created on the specified date
        user_sleep_data = SleepRecord.query.filter_by(user_id = currentuser, date_created = date).all()
        #Iterates through the sleep records and sums up the hours with minutes being converted into hours
        for x in user_sleep_data:
            day_sleep_hours = day_sleep_hours+ int(x.hours_slept) +(x.minutes_slept/60)
        return day_sleep_hours

class WeightGraph(Graph):
    '''
    A class used to represent a graph that displays the user's weight data
    '''
    def __init__(self,timeframe):
        Graph.__init__(self,timeframe)
        self.title = "Weight graph"
        self.linename1 = "Weight (kg)"
        self.linename2 = "Weight goal (kg)"
        self.desired_goal = goals.weight_goal

    def calculate_daily_values(self, date):
        '''
        Calculates the average value for all the weight records in a day for a user

        Parameters:
            date(str): Indicates the day that the average value need to be calculated for.
        Returns:
            int: The average value amount according to the user's weight records for a date
        '''
        #Gets the average weight from the weight records created on the specified date
        average_weight_value = db.session.query(func.avg(WeightRecord.weight)).group_by(WeightRecord.user_id, WeightRecord.date_created).having(WeightRecord.user_id == currentuser,WeightRecord.date_created == date).scalar()

        #if there is weight data return the average weight for the day, if not return 0
        if average_weight_value != None:
            return average_weight_value
        else:
            return 0

class GraphManager:
    '''
    A class to manage all of the graphs for a user.

    Attributes:
        graphs(dictionary): Contains a uri for each of the different types of graph possible for a user
    '''
    def __init__(self):
        self.graphs = {
            "diet" : self.create_graphs(MealGraph),
            "exercise" : self.create_graphs(ExerciseGraph),
            "sleep" : self.create_graphs(SleepGraph),
            "weight" : self.create_graphs(WeightGraph)
        }

    def create_graphs(self, graph_type):
        '''
        Creates all the necessary graphs for a specific graph type.
        This should create three graphs - one for each possible time period.

        Parameters:
            graph_type(db.Model): Indicates the type of graph to create.
        Returns:
            dictionary: Contains the uri for each created graph, with the key being the time period.
        '''
        day = graph_type("day")
        week = graph_type("week")
        month = graph_type("month")

        #Creates encoded data uris for a graph for each time period that'll be embedded in the home page html
        day_graph_uri = day.create_graph().render_data_uri()
        week_graph_uri = week.create_graph().render_data_uri()
        month_graph_uri = month.create_graph().render_data_uri()

        graphs = {
            "day": day_graph_uri,
            "week": week_graph_uri,
            "month": month_graph_uri
        }

        return graphs
