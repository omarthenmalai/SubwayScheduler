from flask import Flask, render_template, request, url_for, redirect
from flask_nav import Nav
from flask_nav.elements import Navbar, Subgroup, View, Link, Text, Separator
from src.service import MapService, ScheduleService
from src.repository import MapRepository, ScheduleRepository

app = Flask(__name__)
nav = Nav(app)
nav.register_element('navbar',
                     Navbar('nav',
                            View('Home Page', 'index'),
                            View('Lines', 'lines'),
                            # View('Schedules', 'schedule'),
                            View('Delays', 'delays')
                            # Separator()
                            )
                     )

map_service = MapService()
schedule_service = ScheduleService()
user_type = "admin"


@app.route("/", methods=["GET"])
def index():
    # temp = map_service.get_station_by_station_name(station_name="Liberty Av")
    if request.method == "GET":
        stations = map_service.get_all_active_stations()
        print(stations)
        return render_template("index.html", stations=stations)
    else:
        return "Error"


@app.route("/login", methods=["POST"])
def login():
    return "Login"


@app.route("/plan_trip", methods=["GET"])
def plan_trip():
    try:
        start_station = eval(request.args.get("start_station"))
        end_station = eval(request.args.get("end_station"))
    except TypeError:
        return "ERROR: Invalid query string"

    start_name = start_station[0]
    start_entrance = start_station[1]

    end_name = end_station[0]
    end_entrance = end_station[1]

    start = map_service.get_station_by_name_and_entrance(station_name=start_name,
                                                         entrance=start_entrance)
    end = map_service.get_station_by_name_and_entrance(station_name=end_name,
                                                       entrance=end_entrance)
    shortest_path, times = map_service.get_shortest_path(start_station=start, stop_station=end)
    if shortest_path is None or len(times) == 0:
        return "Could not find a path!"
    else:
        return render_template("shortest_path.html",
                               train_lines=shortest_path)


@app.route("/lines", methods=["GET"])
def lines():
    if request.args.get("line") is not None:
        line = str(request.args.get("line")).upper()
        stations = map_service.get_stations_by_line(line)
        return render_template("stations_by_line.html",
                               line=line,
                               stations=stations,
                               user_type=user_type)
    else:
        lines = MapRepository().get_distinct_lines()
        lines = sorted([record["lines"] for record in lines if record["lines"] != "6X" and record["lines"] != "7X"])
        return render_template("lines.html",
                               lines=lines)


@app.route("/schedules", methods=["GET"])
def schedules():
    return "Schedules"


@app.route("/delays", methods=["GET"])
def delays():
    delayed_schedules = schedule_service.get_delays()
    return render_template("delays.html",
                           delayed_schedules=delayed_schedules)



@app.route('/<line>/<station_name>/<entrance>')
def change_station_status(line, station_name, entrance):
    station = map_service.get_station_by_name_and_entrance(station_name=station_name,
                                                           entrance=entrance)
    if station.status == "Normal":
        map_service.set_station_status_out_of_order(station)
    else:
        map_service.set_station_status_normal(station)
    return redirect(url_for("lines", line=line))


if __name__ == "__main__":
    app.run(debug=True)