# Import the dependencies.
import sqlalchemy as sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, func, desc

from flask import Flask, jsonify

import datetime as dt

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
Base.prepare(autoload_with = engine)

# reflect the tables
print(Base.classes.keys())

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(bind = engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Common Functions
#################################################

#################################################
# startDateForPrevious12Months() 
# Lookup start date of previous 12 months
#################################################
def startDateForPrevious12Months():
    # Query the most recent date
    recent_date = session.query(Measurement.date).order_by(desc(Measurement.date)).first()
    
    # Convert to datetime object
    recent_date_dt = dt.datetime.strptime(recent_date[0], '%Y-%m-%d') 
    
    # Find the date going back to 12 months from the most recent date
    date_one_year_from_last = recent_date_dt - dt.timedelta(days = 365)

    return date_one_year_from_last.date()

#################################################
# fetch_temparature_stats() 
# Fetch Temparature stats - min, avg and max
# given start date and end date 
# end date is an optional parameter
#################################################
def fetch_temparature_stats(start_date, end_date=None):
    
    # Fetch temparature stats - min, avg, and max for
    # start date and end date
    if(end_date is not None) : 
        temp_stats = session.query(func.min(Measurement.tobs),
                                   func.avg(Measurement.tobs),
                                   func.max(Measurement.tobs)).filter(
                    Measurement.date >= start_date).filter(
                        Measurement.date <= end_date).all()
        # Create the disctionary from the result
        temp_stats_dict = dict({'start_date' : start_date,
                            'end_date' : end_date,
                            'TMIN' : temp_stats[0][0],
                            'TAVG' : temp_stats[0][1],
                            'TMAX' : temp_stats[0][2]})
    else:
        # Fetch temparature stats - min, avg, and max for
        # start date 
        temp_stats = session.query(func.min(Measurement.tobs), 
                                   func.avg(Measurement.tobs),
                                   func.max(Measurement.tobs)).filter(
                    Measurement.date >= start_date).all()
        # Create the disctionary from the result
        temp_stats_dict = dict({'start_date' : start_date,
                            'TMIN' : temp_stats[0][0],
                            'TAVG' : temp_stats[0][1],
                            'TMAX' : temp_stats[0][2]})
    
    return temp_stats_dict
    
            
    
    
#################################################
# Flask Routes
#################################################

#################################################
#  Home Route
#################################################

@app.route("/")
def default():
    print("Server received request for 'default' route..")
    message = """
            Available Routes: <br> <br>
            /api/v1.0/precipitation - returns Precipitation data <br> <br>
            /api/v1.0/stations - returns a list of Stations <br> <br>
            /api/v1.0/tobs - returns a list of temperature observations for the previous year <br> <br>
            /api/v1.0/<start> - returns a list of the minimum temperature, the average temperature, and the maximum temperature for a specified start date <br> <br>
            /api/v1.0/<start>/<end> - - returns a list of the minimum temperature, the average temperature, and the maximum temperature for a specified start and end date (inclusive) <br> <br>
            """
    return message

#################################################
#  Precipitation Route
#################################################

@app.route("/api/v1.0/precipitation")
# Convert the query results from precipitation analysis 
#  (i.e. retrieve only the last 12 months of data) to a dictionary 
#  using date as the key and prcp as the value.
# Return the JSON representation of your dictionary.
def precipitation_func():
    
    print("Server received request for 'precipitation' route..")
    
    # Find the starting date of last 12 months 
    date_one_year_from_last = startDateForPrevious12Months()
    
    # Query for last 12 months of precipitation data
    precipitation_scores = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= date_one_year_from_last).all()
    
    # declare a list to store precipitation data in a dictionary
    precipitation_data = []
    
    # Loop thru the results of precipitation query
    # Create a dictionary containining precipitation data and 
    # append it to the list (Using List Comprehension)
    precipitation_data = [dict({"date" : p[0], "prcp": p[1]}) for p in precipitation_scores]
        
    # Return JSON representation of list of dictionaries that contains precipitation data
    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
#Return a JSON list of stations from the dataset.
def stations_func():
    
    print("Server received request for 'station' route..")
    
    station_list = []
    # Query station table
    station_results = session.query(Station.name).all()
    
    # Create list of stations from the query results
    station_list  = [ s[0] for s in station_results]
    
    # Create the dictionary     
    station_dict = dict({"stations" : station_list})
    
    print(station_dict)
    
    # Return JSON representation of list of stations
    return jsonify(station_dict)


@app.route("/api/v1.0/tobs")
# Query the dates and temperature observations of 
# the most-active station for the previous year of data.
# Return a JSON list of temperature observations for the previous year.
def tobs_func():
    print("Server received request for 'tobs' route..")
    
     # Find the starting date of last 12 months 
    date_one_year_from_last = startDateForPrevious12Months()
    
    # Query for the most active stations in the Measurement table
    most_active_stations = session.query(
        Measurement.station,func.count(
            Measurement.station).label('station_count')).group_by(
        Measurement.station).order_by(desc('station_count'))
    
    # Get the most active station        
    most_active_station=most_active_stations[0][0]
    
    print(most_active_station)
    # Query for temperature obserations for most active station
    # in the previous 12 months
    most_active_station_tobs = session.query(
        Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station).filter(
        Measurement.date >= date_one_year_from_last).all()
    
    # Loop thru the results and create a list of dictionary objects
    tobs = [dict({'date': t[0], 'tobs' : t[1]}) for t in most_active_station_tobs ]
   
    # Return JSNO representation of the list of dictionary objects that contains Temperature Observation data
    return jsonify(tobs)


@app.route("/api/v1.0/<start>")
# Return a JSON list of the minimum temperature, 
# the average temperature, and the maximum temperature 
# for a specified start date
def temperature_stats_start_func(start):
    
    print("Server received request for temperature stats route..")
    print(f"params received start={start}")
    
    # Input validation - Make sure date provided is in YYYY-MM-DD format
    # Otherwise return error
    try:
        dt.datetime.strptime(start, "%Y-%m-%d")
    except ValueError :
            return "Date format accepted is YYYY-MM-DD"
        
    # Fetch temparature stats for given start date
    temp_stats_data = fetch_temparature_stats(start)
    
    # Return JSON representation of data
    return jsonify(temp_stats_data)

@app.route("/api/v1.0/<start>/<end>")
# Return a JSON list of the minimum temperature, 
# the average temperature, and the maximum temperature 
# for a specified start date and end date
def temperature_stats_start_end_func(start, end):
    
    print("Server received request for temperature stats route..")
    print(f"params received start={start}, end={end}")
    
    # Input validation 
    # 1. Make sure date provided is in YYYY-MM-DD format
    #       Otherwise return error
    # 2. Make sure start date is greater than end date
    #       Otherwise return error
    try:
        if (dt.datetime.strptime(start, "%Y-%m-%d") > dt.datetime.strptime(end, "%Y-%m-%d")) :
            return f"Error Start Date {start} provided is greater than End Date {end}!"
    except ValueError :
            return "Date format accepted is YYYY-MM-DD"
        
    # Fetch temparature stats for given start date
    temp_stats_data = fetch_temparature_stats(start, end)
    
    # Return JSON representation of data
    return jsonify(temp_stats_data)


# Run the application 
if __name__ == "__main__":
    app.run(debug=True)
    

@app.teardown_appcontext
def shutdown_session(exception=None):
    session.close()
    print("session closed")