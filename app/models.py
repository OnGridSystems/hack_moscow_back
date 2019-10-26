from app import db


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    cost = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    dimension = db.Column(db.String(50))
    
    shipper_id = db.Column(db.Integer, db.ForeignKey('shipper.id'))
    carrier_id = db.Column(db.Integer, db.ForeignKey('carrier.id'))
    secret = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return f'Order {self.cost} {self.weight}'

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
