from app import db


class OrderStatus:
    NOT_SENT = 'NOT_SENT'
    CANCELLED = 'CANCELLED'
    ON_THE_WAY = 'ON_THE_WAY'
    DELIVERED = 'DELIVERED'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reward = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    dimensions = db.Column(db.String(50))
    pickup_location = db.Column(db.String(50))
    destination = db.Column(db.String(50))
    distance = db.Column(db.Integer)
    coverage = db.Column(db.Integer)
    shipment_date = db.Column(db.String(50))
    delivery_date = db.Column(db.String(50))
    shipper_id = db.Column(db.Integer, db.ForeignKey('shipper.id'))
    carrier_id = db.Column(db.Integer, db.ForeignKey('carrier.id'))
    secret = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(15))
    phone = db.Column(db.String(15))

    def get_json(self, role):
        data = {
            'id': self.id,
            'status': self.status,
            'pickupLocation': self.pickup_location,
            'destination': self.destination,
            'distance': self.distance,
            'dimensions': self.dimensions,
            'weight': self.weight,
            'coverage': self.coverage,
            'reward': self.reward,
            'shipmentDate': self.shipment_date,
            'deliveryDate': self.delivery_date,
            'distance': self.distance,
            'reward': self.reward,
            'phone': self.phone,
        }
        if role == 'SHIPPER':
            data['orderSecret'] = self.secret
        if self.carrier:
            data['carrier'] = self.carrier.username

        return data

    def __repr__(self):
        return f'Order {self.reward} {self.weight}'


class Shipper(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    token = db.Column(db.String(50), unique=True)

    balance = db.Column(db.Integer)

    address = db.Column(db.String(100))

    orders = db.relationship('Order', backref='shipper', lazy=True)

    def get_role(self):
        return 'SHIPPER'

    def __repr__(self):
        return f'Shipper {self.username} {self.password} {self.id}'


class Carrier(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    token = db.Column(db.String(50), unique=True)

    balance = db.Column(db.Integer)
    locked = db.Column(db.Integer)

    address = db.Column(db.String(100))
    vehicle = db.Column(db.String(100))
    max_load = db.Column(db.Integer)

    orders = db.relationship('Order', backref='carrier', lazy=True)

    def get_role(self):
        return 'CARRIER'

    def __repr__(self):
        return f'Carrier {self.username} {self.password} {self.id}'
