from flask import Flask
from src.service import MapService

app = Flask(__name__)

map_service = MapService()


@app.route("/")
def index():
    temp = map_service.get_station_by_station_name(station_name="Liberty Av")
    return temp.to_dict()


if __name__ == "__main__":
    app.run(debug=True)
