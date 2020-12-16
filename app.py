from flask import Flask, render_template, request, url_for, redirect, flash
from flask_login import login_user, current_user, logout_user, login_required, LoginManager
from flask_nav import Nav
from flask_nav.elements import Navbar, Subgroup, View, Link, Text, Separator
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from src.forms import LoginForm, RegistrationForm
from src.service import MapService, ScheduleService, UserService, TripService
from src.repository import MapRepository, ScheduleRepository, UserRepository
from src.models import User, Schedule, Trip, SubwayStation, TrainLine
from src import app

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
user_service = UserService()
trip_service = TripService()


@app.route("/", methods=["GET"])
@login_required
def index():
    if current_user.is_authenticated:
        stations = map_service.get_all_active_stations()
        return render_template("index.html", stations=stations)
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = user_service.login_user(form.email.data, form.password.data)
            login_user(user, remember=form.remember.data)
            flash('You have been logged in!', 'success')
            # next_page = request.args.get('next')
            return redirect(url_for('index'))
        except (AttributeError, IntegrityError):
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = user_service.add_user(User(form.email.data, form.password.data, False))
        if user is not None:
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        else:
            flash('This email is already registered, please log in or choose a different email', 'danger')
    return render_template('register.html', title='Register', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/plan-trip", methods=["GET"])
@login_required
def plan_trip():
    if current_user.is_authenticated:
        try:
            start_station = eval(request.args.get("start_station"))
            end_station = eval(request.args.get("end_station"))
        except TypeError:
            return "ERROR: Invalid query string"

        # extract station properties from query string
        start_name = start_station[0]
        start_entrance = start_station[1]

        end_name = end_station[0]
        end_entrance = end_station[1]

        # Get the starting and ending stations
        start = map_service.get_station_by_name_and_entrance(station_name=start_name,
                                                             entrance=start_entrance)
        end = map_service.get_station_by_name_and_entrance(station_name=end_name,
                                                           entrance=end_entrance)

        # Get the shortest path
        shortest_path, times = map_service.get_shortest_path(start_station=start, stop_station=end)
        if shortest_path is None or len(times) == 0:
            return "Could not find a path!"
        else:
            return render_template("shortest_path.html",
                                   train_lines=shortest_path)
    else:
        return redirect(url_for("login"))


@app.route("/lines", methods=["GET"])
@login_required
def lines():
    if current_user.is_authenticated:
        if request.args.get("line") is not None:
            line = str(request.args.get("line")).upper()
            stations = map_service.get_stations_by_line(line)
            return render_template("stations_by_line.html",
                                   line=line,
                                   stations=stations,
                                   is_admin=current_user.is_admin)
        else:
            # Get the distinct lines in the GraphDB
            lines = map_service.get_distinct_lines()

            # Get the unique pair of line and direction in ScheduleDB
            line_direction_combos = schedule_service.get_unique_line_direction()

            lines = sorted([record["lines"] for record in lines if record["lines"] != "6X" and record["lines"] != "7X"])
            return render_template("lines.html",
                                   lines=lines,
                                   schedules=line_direction_combos)
    else:
        return redirect(url_for("login"))


@app.route("/schedules", methods=["GET"])
@login_required
def schedules():
    line = request.args.get("line")
    direction = request.args.get("direction")
    if line is None or direction is None:
        return "Invalid query string. Could not get the desired schedule."
    else:
        stations, schedules = schedule_service.get_schedules_by_line_direction(line, direction)
        return render_template("schedule.html",
                               stations=stations,
                               schedules=schedules,
                               line=line,
                               direction=direction,
                               is_admin=current_user.is_admin)


@app.route("/delay-train", methods=["POST"])
@login_required
def delay_train():
    if not current_user.is_admin:
        flash("Only admins can do this action.", "danger")
        return redirect(url_for("lines"))
    else:
        form = request.form
        station_name = form["station"]
        delay = form["delay"]
        starting_station = form["starting_station"]
        time = datetime.strptime(form["time"], "%H:%M")
        direction = form["direction"]
        line = form["line"]


        schedule = schedule_service.get_train_by_line_direction_station_and_start_time(line, direction,
                                                                                       starting_station, time)
        schedule_service.delay_train(schedule, station_name, timedelta(minutes=int(delay)))

        return redirect(url_for("schedules", line=line, direction=direction))


@app.route("/remove-delay/<line>/<direction>/<time>/<starting_station>")
@login_required
def remove_delay(line, direction, time, starting_station):
    if not current_user.is_admin:
        flash("Only admins can do this action.", "danger")
        return redirect(url_for("lines"))
    else:
        time = datetime.strptime(time, "%H:%M")


        # Get the schedule with the delay
        schedule = schedule_service.get_train_by_line_direction_station_and_start_time(line=line,
                                                                                       direction=direction,
                                                                                       starting_station=starting_station,
                                                                                       time=time)
        schedule_service.remove_delay(schedule)
        return redirect(url_for("delays"))


@app.route("/delays", methods=["GET"])
@login_required
def delays():
    delayed_schedules = schedule_service.get_delays()
    if len(delayed_schedules) == 0:
        delayed_schedules = None
    return render_template("delays.html",
                           delayed_schedules=delayed_schedules,
                           is_admin=current_user.is_admin)



@app.route('/log-trip/<start_name>/<start_entrance>/<stop_name>/<stop_entrance>/<start_time>/<stop_time>', methods=["GET"])
@login_required
def log_trip(start_name, start_entrance, stop_name, stop_entrance, start_time, stop_time):
    time = (datetime.strptime(stop_time, "%H:%M") - datetime.strptime(start_time, "%H:%M")).seconds//60
    trip = Trip(user_id=current_user.user_id, start="{}, {}".format(start_name, start_entrance),
                stop="{}, {}".format(stop_name, stop_entrance), time=time)
    trip_service.add_trip(trip=trip)


    return redirect(url_for('index'))


@app.route('/trips', methods=["GET"])
@login_required
def trips():
    trips = trip_service.get_trips_by_user_id(current_user.user_id)
    if len(trips) == 0:
        return render_template('trips.html', trips=None)
    else:
        return render_template('trips.html', trips=trips)


@app.route('/change-status/<line>/<station_name>/<entrance>')
@login_required
def change_station_status(line, station_name, entrance):
    if current_user.is_admin:
        station = map_service.get_station_by_name_and_entrance(station_name=station_name,
                                                               entrance=entrance)
        if station.status == "Normal":
            map_service.set_station_status_out_of_order(station)
        else:
            map_service.set_station_status_normal(station)
    else:
        flash("Only administrators can change a station's status!")
    return redirect(url_for("lines", line=line))


if __name__ == "__main__":
    app.run(debug=True)
