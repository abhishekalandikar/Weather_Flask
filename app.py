import datetime
import os

import requests
import sys

from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy

# Generate private session key
key = os.urandom(24)

# Initialize app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
app.config["DEBUG"] = True

OPENWEATHERMAP_API_KEY = "271ddc87c594ffe4288d82539ebf4c2a"  # Please paste your API key here
app.secret_key = key

db = SQLAlchemy(app)


# Create database model
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Return name to be queried in requests to the api
    def __repr__(self):
        return self.name


@app.route("/")
def index():
    # Get the current time zone
    def get_time_zone(timezone):
        tz = datetime.timezone(datetime.timedelta(seconds=int(timezone)))
        return datetime.datetime.now(tz=tz).time().hour

    # Query all entries from the database
    cities = City.query.all()
    weather = []

    for city in cities:
        # Request the weather data from the API
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric")

        # Get the weather data from the response
        content = response.json()

        # Build the weather data
        weather_info = {"city": content["name"],
                        "degrees": int(content["main"]["temp"]),
                        "state": content["weather"][0]["description"],
                        "time": get_time_zone(content["timezone"]),
                        "id": city.id}

        # Add the weather data to the list
        weather.append(weather_info)

    return render_template("index.html", weather=weather)


@app.route("/add", methods=["POST"])
def add_city():
    if request.method == 'POST':
        # Get the city name from the form
        city_name = request.form.get("city_name")

        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHERMAP_API_KEY}&units=metric")

        if response.status_code == 404:
            flash("The city doesn't exist!")
            return redirect("/")

        # Check if the city already exists
        if City.query.filter_by(name=city_name).first() is not None:
            flash("The city has already been added to the list!")
            return redirect("/")

        # Create a new city and commit it to the database
        city = City(name=city_name)
        db.session.add(city)
        db.session.commit()
        return redirect("/")


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with app.app_context():
            db.create_all()
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        with app.app_context():
            db.create_all()
        app.run()
