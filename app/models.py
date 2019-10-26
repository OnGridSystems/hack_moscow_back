from app import db


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # stats
    cost = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    dimension = db.Column(db.String(50))
    
    # relationships
    # carrier = 
    # shipper =

    # , index=True, unique=True


class Shipper(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    token = db.Column(db.String(50), unique=True)

    address = db.Column(db.String(100))

    def __repr__(self):
        return f'{self.username} {self.password} {self.id}'

class Carrier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    token = db.Column(db.String(50), unique=True)

    deposit = db.Column(db.Integer)
    locked = db.Column(db.Integer)

    address = db.Column(db.String(100))

    def __repr__(self):
        return f'{self.username} {self.password} {self.id}'
