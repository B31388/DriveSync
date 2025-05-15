from abc import ABC, abstractmethod
from geopy.distance import geodesic

class Account(ABC):
    def __init__(self, account_id, name, email, contact):
        self._account_id = account_id
        self._name = name
        self._email = email
        self._contact = contact

    @property
    def account_id(self):
        return self._account_id

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

    @property
    def contact(self):
        return self._contact

    @abstractmethod
    def get_details(self):
        pass

    @abstractmethod
    def account_type(self):
        pass

class Vehicle:
    def __init__(self, vehicle_type, vehicle_reg_no, fuel_litres_per_km, daily_vehicle_charges):
        self.vehicle_type = vehicle_type
        self.vehicle_reg_no = vehicle_reg_no
        self.fuel_litres_per_km = fuel_litres_per_km
        self.daily_vehicle_charges = daily_vehicle_charges

    def get_cost_profile(self):
        return {
            "fuel_litres_per_km": self.fuel_litres_per_km,
            "daily_vehicle_charges": self.daily_vehicle_charges
        }

class Driver(Account):
    def __init__(self, account_id, name, email, contact,
                 vehicle_type, vehicle_reg_no,
                 driver_day_allowance, driver_night_allowance):
        super().__init__(account_id, name, email, contact)
        self.vehicle_type = vehicle_type
        self.vehicle_reg_no = vehicle_reg_no
        self._driver_day_allowance = driver_day_allowance
        self._driver_night_allowance = driver_night_allowance
        self._vehicle = None

    @property
    def vehicle(self):
        return self._vehicle

    @vehicle.setter
    def vehicle(self, vehicle_obj):
        self._vehicle = vehicle_obj

    @property
    def driver_day_allowance(self):
        return self._driver_day_allowance

    @property
    def driver_night_allowance(self):
        return self._driver_night_allowance

    def get_details(self):
        vehicle_info = f"Vehicle Reg: {self.vehicle.vehicle_reg_no}" if self.vehicle else "No Vehicle Assigned"
        return (
            f"Driver ID: {self.account_id}, Name: {self.name}, "
            f"{vehicle_info}, Day Allowance: UGX {self.driver_day_allowance}, "
            f"Night Allowance: UGX {self.driver_night_allowance}"
        )

    def assign_trip(self, trip):
        return f"🚚 Driver {self.name} assigned to trip from {trip.start_location} to {trip.end_location}"

    def account_type(self):
        return "Driver"

class Client(Account):
    def __init__(self, account_id, name, email, contact):
        super().__init__(account_id, name, email, contact)
        self._trip_cost = 0.0

    @property
    def trip_cost(self):
        return self._trip_cost

    @trip_cost.setter
    def trip_cost(self, value):
        self._trip_cost = value

    def request_trip(self, trip):
        self._trip_cost = trip.total_cost
        return f"🛣️ Client {self.name} requested trip. Estimated cost: UGX {self.trip_cost:,.2f}"

    def get_details(self):
        return f"Client ID: {self.account_id}, Name: {self.name}"

    def account_type(self):
        return "Client"

class ClientRequest:
    def __init__(self, name, email, contact, goods_description, pick_up_point, drop_off_point, comments, estimated_cost=0.0, client_id=None, pick_up_name=None, drop_off_name=None):
        self.name = name
        self.email = email
        self.contact = contact
        self.goods_description = goods_description
        self.pick_up_point = pick_up_point
        self.drop_off_point = drop_off_point
        self.comments = comments
        self.estimated_cost = estimated_cost
        self.client_id = client_id
        self.pick_up_name = pick_up_name
        self.drop_off_name = drop_off_name

    def get_details(self):
        return (
            f"Name: {self.name}, Email: {self.email}, Contact: {self.contact}, "
            f"Goods: {self.goods_description}, Pick-up: {self.pick_up_point}, "
            f"Drop-off: {self.drop_off_point}, Comments: {self.comments}, "
            f"Estimated Cost: UGX {self.estimated_cost}"
        )

class Trip:
    def __init__(self, start_location, end_location, fuel_cost, vehicle: Vehicle, driver: Driver, client_id=None):
        self.start_location = start_location
        self.end_location = end_location
        self.fuel_cost = fuel_cost
        self.vehicle = vehicle
        self.driver = driver
        self.client_id = client_id
        self._distance = self.calculate_distance()
        self._total_cost = self.calculate_cost()

    def calculate_distance(self):
        try:
            if not (isinstance(self.start_location, tuple) and isinstance(self.end_location, tuple)):
                raise ValueError("Locations must be tuples of (latitude, longitude)")
            if not all(isinstance(coord, (int, float)) for coord in self.start_location + self.end_location):
                raise ValueError("Coordinates must be numeric")
            distance = geodesic(self.start_location, self.end_location).km
            if distance < 0:
                raise ValueError("Calculated distance is negative")
            return distance
        except Exception as e:
            print(f"❌ Error calculating distance: {e}")
            return 0

    def calculate_cost(self):
        fuel_expense = self._distance * self.vehicle.fuel_litres_per_km * self.fuel_cost
        total = (
            fuel_expense +
            self.driver.driver_day_allowance +
            self.driver.driver_night_allowance +
            self.vehicle.daily_vehicle_charges
        )
        return total

    @property
    def distance(self):
        return self._distance

    @property
    def total_cost(self):
        return self._total_cost