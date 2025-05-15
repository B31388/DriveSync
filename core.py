from models import Vehicle, Driver, Client, Trip, Account, ClientRequest

class DriveSyncApp:
    def __init__(self):
        self.drivers = []
        self.clients = []
        self.vehicles = []
        self.trips = []
        self.client_requests = []
        # Default for cost estimation
        self.default_vehicle = Vehicle("Van", "DEFAULT001", fuel_litres_per_km=0.1, daily_vehicle_charges=50000)
        self.default_driver = Driver(
            account_id="D000",
            name="Default Driver",
            email="default@example.com",
            contact="0000000000",
            vehicle_type="Van",
            vehicle_reg_no="DEFAULT001",
            driver_day_allowance=10000,
            driver_night_allowance=15000
        )
        self.default_driver.vehicle = self.default_vehicle

    def onboard_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)

    def add_account(self, account: Account):
        if isinstance(account, Driver):
            self.drivers.append(account)
        elif isinstance(account, Client):
            self.clients.append(account)

    def add_client_request(self, request: ClientRequest):
        self.client_requests.append(request)
        # Estimate cost
        try:
            trip = Trip(
                start_location=request.pick_up_point,
                end_location=request.drop_off_point,
                fuel_cost=5000,  # Default fuel cost
                vehicle=self.default_vehicle,
                driver=self.default_driver
            )
            request.estimated_cost = trip.total_cost
        except Exception as e:
            request.estimated_cost = 0.0
            print(f"Cost estimation failed: {e}")
        # Create a client if not exists
        client = next((c for c in self.clients if c.email == request.email), None)
        if not client:
            account_id = f"C{len(self.clients) + 1:03d}"
            client = Client(account_id, request.name, request.email, request.contact)
            self.add_account(client)
        return client

    def process_trip(self, client_id, driver_id, start, end, fuel_cost):
        client = next((c for c in self.clients if c.account_id == client_id), None)
        driver = next((d for d in self.drivers if d.account_id == driver_id), None)

        if not (client and driver):
            return "⚠️ Client or Driver not found"

        if not driver.vehicle:
            return "⚠️ Driver has no vehicle assigned"

        trip = Trip(start, end, fuel_cost, driver.vehicle, driver, client_id=client_id)
        self.trips.append(trip)

        driver.assign_trip(trip)
        result = client.request_trip(trip)
        return f"{result} (Total Cost: UGX {trip.total_cost:,.2f})"

    def list_all_accounts(self):
        return [f"{acc.account_type()}: {acc.get_details()}" for acc in self.drivers + self.clients]