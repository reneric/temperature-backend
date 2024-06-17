from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import plotly.express as px
import pandas as pd
import pytz
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://admin:admin@db:5432/temperature_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
CORS(app)


class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<Temperature {self.temperature}C, {self.humidity}%>"


@app.route("/temperature", methods=["POST"])
def add_temperature():
    data = request.get_json()
    if "temperature" not in data or "humidity" not in data:
        return jsonify({"error": "Invalid data"}), 400

    temperature = Temperature(
        temperature=data["temperature"], humidity=data["humidity"]
    )
    db.session.add(temperature)
    db.session.commit()

    return jsonify({"message": "Temperature added"}), 201


@app.route("/temperature", methods=["GET"])
def get_temperatures():
    temperatures = Temperature.query.all()
    results = [
        {
            "temperature": temp.temperature,
            "humidity": temp.humidity,
            "timestamp": temp.timestamp,
        }
        for temp in temperatures
    ]

    return jsonify(results)


@app.route("/temperature/graph", methods=["GET"])
def get_temperature_graph():
    temperatures = Temperature.query.order_by(Temperature.timestamp).all()
    if not temperatures:
        return "No temperature data available to display."

    central = pytz.timezone("America/Chicago")

    data = [
        {
            "temperature": temp.temperature,
            "humidity": temp.humidity,
            "timestamp": temp.timestamp.astimezone(central).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
        for temp in temperatures
    ]

    df = pd.DataFrame(data)

    if df.empty:
        return "No data to plot."

    # Get the latest temperature and humidity
    latest_temp = data[-1]["temperature"]
    latest_humidity = data[-1]["humidity"]

    fig = px.line(
        df,
        x="timestamp",
        y=["temperature", "humidity"],
        title="Garage Temperature and Humidity",
    )
    graph_html = fig.to_html(full_html=False)

    return render_template_string(
        """
    <html>
        <head>
            <title>Temperature and Humidity Graph</title>
            <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='style.css') }}">
        </head>
        <body>
            <h3>{{ latest_temp }}°F | {{ latest_humidity }}%</h3>
            {{ graph_html | safe }}
        </body>
    </html>
    """,
        latest_temp=latest_temp,
        latest_humidity=latest_humidity,
        graph_html=graph_html,
    )


@app.route("/test")
def test_page():
    return render_template_string(
        """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>This is a test page</h1>
        </body>
    </html>
    """
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
