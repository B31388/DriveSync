from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, NumberRange
from core import DriveSyncApp
from models import Vehicle, Driver, Client, ClientRequest

flask_app = Flask(__name__)
flask_app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with env variable in production
logic = DriveSyncApp()

# Predefined locations (latitude, longitude) for Uganda
LOCATIONS = [
    ('Kampala', (0.3476, 32.5825)),
    ('Entebbe', (0.3163, 32.3892)),
    ('Jinja', (0.4244, 33.2041)),
    ('Gulu', (2.7746, 32.2990)),
    ('Mbarara', (-0.6072, 30.6545)),
    ('Fort Portal', (0.6710, 30.2750)),
    ('Arua', (3.0201, 30.9111)),
    ('Mbale', (1.0784, 34.1750))
]

# Custom Jinja2 filter for formatting numbers
def format_number(value):
    try:
        return "{:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return value

flask_app.jinja_env.filters['format_number'] = format_number

# WTForms for validation
class ClientForm(FlaskForm):
    account_id = StringField('Account ID', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact = StringField('Contact', validators=[DataRequired()])
    submit = SubmitField('Create Client')

class DriverForm(FlaskForm):
    account_id = StringField('Account ID', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact = StringField('Contact', validators=[DataRequired()])
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('', 'Select Vehicle Type'),
        ('Van', 'Van'),
        ('Truck', 'Truck'),
        ('Car', 'Car'),
        ('Bus', 'Bus')
    ], validators=[DataRequired()])
    vehicle_reg_no = SelectField('Vehicle Registration Number', validators=[DataRequired()])
    driver_day_allowance = FloatField('Day Allowance (UGX)', validators=[DataRequired(), NumberRange(min=0)])
    driver_night_allowance = FloatField('Night Allowance (UGX)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Driver')

    def __init__(self, vehicles, *args, **kwargs):
        super(DriverForm, self).__init__(*args, **kwargs)
        self.vehicle_reg_no.choices = [('', 'Select Vehicle')] + [(v.vehicle_reg_no, v.vehicle_reg_no) for v in vehicles]

class VehicleForm(FlaskForm):
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('', 'Select Vehicle Type'),
        ('Van', 'Van'),
        ('Truck', 'Truck'),
        ('Car', 'Car'),
        ('Bus', 'Bus')
    ], validators=[DataRequired()])
    vehicle_reg_no = StringField('Vehicle Registration Number', validators=[DataRequired()])
    fuel_litres_per_km = FloatField('Fuel Litres per KM', validators=[DataRequired(), NumberRange(min=0)])
    daily_vehicle_charges = FloatField('Daily Vehicle Charges (UGX)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Vehicle')

class TripForm(FlaskForm):
    client_id = SelectField('Client ID', validators=[DataRequired()])
    driver_id = SelectField('Driver ID', validators=[DataRequired()])
    start_location = SelectField('Start Location', choices=[('', 'Select Start Location')] + [(loc[0], loc[0]) for loc in LOCATIONS])
    start_location_lat = FloatField('Start Latitude (Override)')
    start_location_lon = FloatField('Start Longitude (Override)')
    end_location = SelectField('End Location', choices=[('', 'Select End Location')] + [(loc[0], loc[0]) for loc in LOCATIONS])
    end_location_lat = FloatField('End Latitude (Override)')
    end_location_lon = FloatField('End Longitude (Override)')
    fuel_cost = FloatField('Fuel Cost per Litre (UGX)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Process Trip')

    def __init__(self, clients, drivers, *args, **kwargs):
        super(TripForm, self).__init__(*args, **kwargs)
        self.client_id.choices = [('', 'Select Client')] + [(c.account_id, f"{c.account_id} - {c.name}") for c in clients]
        self.driver_id.choices = [('', 'Select Driver')] + [(d.account_id, f"{d.account_id} - {d.name}") for d in drivers]

class ClientRequestForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact = StringField('Contact', validators=[DataRequired()])
    goods_description = TextAreaField('Description of Goods', validators=[DataRequired()])
    pick_up_point = SelectField('Pick-up Point', choices=[('', 'Select Pick-up Point')] + [(loc[0], loc[0]) for loc in LOCATIONS], validators=[DataRequired()])
    drop_off_point = SelectField('Drop-off Point', choices=[('', 'Select Drop-off Point')] + [(loc[0], loc[0]) for loc in LOCATIONS], validators=[DataRequired()])
    comments = TextAreaField('Comments')
    submit = SubmitField('Submit Request')

# Routes
@flask_app.route('/')
def home():
    return render_template('index.html', drivers=logic.drivers, clients=logic.clients, accounts=logic.list_all_accounts(), requests=logic.client_requests, trips=logic.trips)

@flask_app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    form = ClientForm()
    if form.validate_on_submit():
        try:
            client = Client(
                account_id=form.account_id.data,
                name=form.name.data,
                email=form.email.data,
                contact=form.contact.data
            )
            logic.add_account(client)
            flash('Client account created successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
    return render_template('create_account.html', form=form)

@flask_app.route('/add_driver', methods=['GET', 'POST'])
def add_driver():
    form = DriverForm(vehicles=logic.vehicles)
    if form.validate_on_submit():
        try:
            driver = Driver(
                account_id=form.account_id.data,
                name=form.name.data,
                email=form.email.data,
                contact=form.contact.data,
                vehicle_type=form.vehicle_type.data,
                vehicle_reg_no=form.vehicle_reg_no.data,
                driver_day_allowance=form.driver_day_allowance.data,
                driver_night_allowance=form.driver_night_allowance.data
            )
            vehicle = next((v for v in logic.vehicles if v.vehicle_reg_no == form.vehicle_reg_no.data), None)
            if vehicle:
                driver.vehicle = vehicle
            else:
                flash('Vehicle not found. Driver added without vehicle assignment.', 'warning')
            logic.add_account(driver)
            flash('Driver added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error adding driver: {str(e)}', 'error')
    return render_template('add_driver.html', form=form)

@flask_app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        try:
            vehicle = Vehicle(
                vehicle_type=form.vehicle_type.data,
                vehicle_reg_no=form.vehicle_reg_no.data,
                fuel_litres_per_km=form.fuel_litres_per_km.data,
                daily_vehicle_charges=form.daily_vehicle_charges.data
            )
            logic.onboard_vehicle(vehicle)
            flash('Vehicle added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error adding vehicle: {str(e)}', 'error')
    return render_template('add_vehicle.html', form=form)

@flask_app.route('/process_trip', methods=['GET', 'POST'])
def process_trip():
    form = TripForm(clients=logic.clients, drivers=logic.drivers)
    if form.validate_on_submit():
        try:
            start_coords = None
            end_coords = None
            if form.start_location.data and form.start_location.data != '':
                start_coords = next(loc[1] for loc in LOCATIONS if loc[0] == form.start_location.data)
            elif form.start_location_lat.data and form.start_location_lon.data:
                start_coords = (form.start_location_lat.data, form.start_location_lon.data)
            
            if form.end_location.data and form.end_location.data != '':
                end_coords = next(loc[1] for loc in LOCATIONS if loc[0] == form.end_location.data)
            elif form.end_location_lat.data and form.end_location_lon.data:
                end_coords = (form.end_location_lat.data, form.end_location_lon.data)
            
            if not (start_coords and end_coords):
                flash('Please provide valid start and end locations.', 'error')
                return render_template('process_trip.html', form=form)

            result = logic.process_trip(
                client_id=form.client_id.data,
                driver_id=form.driver_id.data,
                start=start_coords,
                end=end_coords,
                fuel_cost=form.fuel_cost.data
            )
            if "⚠️" in result:
                flash(result, 'error')
            else:
                flash(result, 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error processing trip: {str(e)}', 'error')
    return render_template('process_trip.html', form=form)

@flask_app.route('/client_request', methods=['GET', 'POST'])
def client_request():
    form = ClientRequestForm()
    if form.validate_on_submit():
        try:
            pick_up_coords = next(loc[1] for loc in LOCATIONS if loc[0] == form.pick_up_point.data)
            drop_off_coords = next(loc[1] for loc in LOCATIONS if loc[0] == form.drop_off_point.data)
            
            client_request = ClientRequest(
                name=form.name.data,
                email=form.email.data,
                contact=form.contact.data,
                goods_description=form.goods_description.data,
                pick_up_point=pick_up_coords,
                drop_off_point=drop_off_coords,
                comments=form.comments.data
            )
            client = logic.add_client_request(client_request)
            return render_template('confirmation.html', 
                                 request=client_request, 
                                 cost=client_request.estimated_cost,
                                 client_name=client.name)
        except Exception as e:
            flash(f'Error submitting request: {str(e)}', 'error')
    return render_template('client_request.html', form=form)

if __name__ == "__main__":
    flask_app.run(debug=True)  # Set debug=False in production