from flask import render_template, url_for, flash, redirect
from subwaymapper import app
from subwaymapper.forms import RegistrationForm, LoginForm
from subwaymapper.models import *
from subwaymapper.service import *
from subwaymapper.repository import *
from flask_login import login_user, current_user, logout_user, login_required
from flask import request

user_service = UserService()
schedule_service = ScheduleService()
Trains = [["1","Bronx-Bound"], ["1","Manhattan-Bound"],
		["2","Bronx-Bound"],["2","Brooklyn-Bound"], 
		["3","Brooklyn-Bound"], ["3","Manhattan-Bound"],
		["4","Bronx-Bound"],["4","Brooklyn-Bound"],
		["5","Bronx-Bound"],["5","Brooklyn-Bound"],
		["6","Bronx-Bound"],["6","Manhattan-Bound"],
		["7","Manhattan-Bound"],["7","Queens-Bound"],
		["A","Manhattan-Bound"],["A","Queens-Bound"],
		["B","Bronx-Bound"],["B","Brooklyn-Bound"],
		["C","Brooklyn-Bound"],["C","Manhattan-Bound"],
		["D","Bronx-Bound"],["D","Brooklyn-Bound"],
		["E","Manhattan-Bound"],["E","Queens-Bound"],
		["F","Brooklyn-Bound"],["F","Queens-Bound"],
		["G","Brooklyn-Bound"],["G","Queens-Bound"],
		["J","Manhattan-Bound"],["J","Queens-Bound"],
		["L","Manhattan-Bound"],["L","Brooklyn-Bound"],
		["M","Brooklyn-Bound"],["M","Queens-Bound"],
		["N","Brooklyn-Bound"],["N","Queens-Bound"],
		["Q","Brooklyn-Bound"],["Q","Manhattan-Bound"],
		["R","Brooklyn-Bound"],["R","Queens-Bound"],
		["W","Manhattan-Bound"],["W","Queens-Bound"]]

i = 0

@app.route('/')
def home():
	return render_template('home.html', title='Home')

@app.route("/register", methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		if user_service.confirm_unique_email(form.email.data):
			user_service.add_user(++i, form.email.data, form.password.data, 0)
			flash('Your account has been created! You are now able to log in', 'success')
			return redirect(url_for('login'))
		else:
			flash('This email is already registered, please log in or choose a different email', 'danger')
	return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		x = user_service.confirm_unique_email(form.email.data)
		if x == False:
			if user_service.login_user(form.email.data,form.password.data):
				flash('You have been logged in!', 'success')
				user = user_service.get_actual_user_by_email(form.email.data)
				login_user(user, remember = form.remember.data)
				next_page = request.args.get('next')
				return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check email and password', 'danger')
	return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('home'))

@app.route("/account")
@login_required
def account():
	return render_template('account.html', title='Account')

@app.route("/about")
def about():
	return render_template('about.html', title='About')

@app.route("/trains")
@login_required
def trains():
	return render_template('trains.html', title='Trains', Trains=Trains)

# Dynamically creates a route for every possible train
@app.route('/trains/<n>')
@login_required
def some_train_page(n):
	split_file_name = n.split('-')
	line = str(split_file_name[0])
	direction = str(split_file_name[-2])
	direction = direction + '-Bound'
	x = schedule_service.get_schedules_by_line_direction(line,direction)
	if len(x) == 0:
		return redirect(url_for('home'))
	else:
		return render_template('train-schedule.html', crown=x, title=n)