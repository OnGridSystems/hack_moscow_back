from app import app, db
from app.models import Order, Shipper, Carrier, OrderStatus
from app.middlewares import session_middleware

from flask import request, jsonify, g
from uuid import uuid4


@app.route('/api/register', methods=['POST'])
def register():
    request_body = request.json
    token = str(uuid4())
    print(f'register : {request_body}')

    role = request_body.get('role')
    username = request_body.get('username')
    password = request_body.get('password')
    address = request_body.get('address')

    if not role in ['SHIPPER', 'CARRIER']:
        return jsonify({'error': 'No role provided'})
    if not username:
        return jsonify({'error': 'No username provided'})
    if not password:
        return jsonify({'error': 'No password provided'})
    if not address and role=='SHIPPER':
        return jsonify({'error': 'No address provided'})

    if (
        not Shipper.query.filter_by(username=username).first()
        and not Carrier.query.filter_by(username=username).first()
    ):
        u = None
        if role == 'SHIPPER':
            u = Shipper(
                username=username,
                password=password,
                token=token,
                address=address,
                balance=0,
            )
        elif role == 'CARRIER':
            vehicle = request_body.get('vehicle')
            max_load = request_body.get('maxLoad')

            if not vehicle:
                return jsonify({'error': 'No role provided'})
            if not max_load:
                return jsonify({'error': 'No role provided'})

            u = Carrier(
                username=username,
                password=password,
                token=token,
                balance=0,
                locked=0,
                vehicle=vehicle,
                max_load=max_load,
            )

        try:
            db.session.add(u)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': e})
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Already registrated'})


@app.route('/api/login', methods=['POST'])
def login():
    request_body = request.json
    username = request_body['username']
    password = request_body['password']

    print(f'login : {request_body}')

    user = Shipper.query.filter_by(username=username).first()
    if not user:
        user = Carrier.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'No such user'})
    
    if user.password == password:
        return jsonify({'token': user.token})


@app.route('/api/user')
@session_middleware
def user_info():
    user = g.user
    role = user.get_role()

    if role == 'SHIPPER':
        return {
            'role': role,
            'username': user.username,
            'balance': user.balance,
            'location': user.address,
        }
    elif role == 'CARRIER':
        return {
            'role': role,
            'username': user.username,
            'balance': user.balance,
            'totalBalance': user.balance,
            'lockedBalance': user.locked,
            'availableBalance': user.balance - user.locked,
            'smartContract': '0xDJKJKDr6yDS7aDdfghjk234567sdfghj',
            'vehicle': user.vehicle,
            'maxLoad': user.max_load,
        }



@app.route('/api/available-orders')
@session_middleware
def available_orders():
    user = g.user
    if user.get_role() == 'SHIPPER':
        return jsonify({'error': 'you have no access'})
    return jsonify(
        [
            o.get_json(user.get_role())
            for o in Carrier.query.filter_by(status=OrderStatus.NOT_SENT)
        ]
    )


@app.route('/api/user/orders', methods=['POST', 'GET'])
@session_middleware
def user_orders():
    user = g.user
    if request.method == 'POST' and user.get_role() == 'SHIPPER':
        request_body = request.json
        
        pickup_location = request_body['pickupLocation']
        destination = request_body['destination']
        dimensions = request_body['dimensions']
        weight = request_body['weight']
        coverage = request_body['coverage']
        shipment_date = request_body['shipmentDate']
        delivery_date = request_body['deliveryDate']
        print(pickup_location, destination, dimensions, weight, coverage, shipment_date, delivery_date)
        if (
            pickup_location
            and destination
            and dimensions
            and weight is not None
            and coverage is not None
            and shipment_date
            and delivery_date
        ):
            seed = pickup_location + destination
            distance = get_distance(seed)
            reward = distance * 10

            o = Order(
                pickup_location=pickup_location,
                destination=destination,
                dimensions=dimensions,
                weight=weight,
                coverage=coverage,
                shipment_date=shipment_date,
                delivery_date=delivery_date,
                status=OrderStatus.NOT_SENT,
                secret=str(uuid4()),
                distance=distance,
                reward=reward,
            )
            user.orders.append(o)
            db.session.add(o)
            db.session.add(user)
            db.session.commit()
            return jsonify({'result': 'success'})
        else:
            return jsonify({'error': 'wrong request'})
    elif request.method == 'GET':
        return jsonify([o.get_json(user.get_role()) for o in user.orders])
    else:
        return jsonify({'error': 'only shipper can create orders'})


def get_distance(seed):
    return int(hashlib.sha1(seed.encode()).hexdigest()[:2], 16)


@app.route('/api/getDeliveryReward')
def get_delivery_reward():
    pickup_location = request.args.get('pickupLocation')
    destination = request.args.get('destination')

    if not destination and not pickup_location:
        return jsonify({'error': 'destination and pickup_locations needs'})

    seed = pickup_location + destination
    return {
        'reward': get_distance(seed)*10
    }


@app.route('/api/orders/<int:order_id>/take', methods=['POST'])
@session_middleware
def take_order(order_id):
    user = g.user
    if user.get_role() == 'CARRIER':
        o = Order.query.filter_by(id=order_id).first()
        if user.balance >= o.coverage:
            user.locked += o.coverage
            user.orders.append(o)
            o.status = OrderStatus.ON_THE_WAY

            db.session.add(o)
            db.session.add(user)
            db.session.commit()

            return jsonify({'info': 'Order taken'})
        else:
            return jsonify({'error': 'your deposit is smaller then coverage'})
    else:
        return jsonify({'error': 'CARRIER role needed'})


@app.route('/api/api/confirm-delivery', methods=['POST'])
def confirm():
    request_body = request.json
    secret = request_body.get('orderSecret')
    if secret:
        o = Order.query.filter_by(secret=secret).first()
        o.status = OrderStatus.DELIVERED
        db.session.add(o)

        user = o.carrier
        user.locked -= o.coverage
        user.reward += o.reward
        db.session.add(user)

        db.session.commit()
    return jsonify({'error': 'no such order'})


@app.route('/api/debug/increase-balance', methods=['POST'])
def balance_increase():
    request_body = request.json
    username = request_body['username']
    amount = request_body['amount']

    user = Shipper.query.filter_by(username=username).first()
    if not user:
        user = Carrier.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'No such user'})

    user.balance += amount
    try:
        db.session.add(u)
        db.session.commit()
    except Exception as e: # TODO: change
        return jsonify({'error': e})
    return jsonify({'status': 200})


@app.route('/api/debug/carriers')
def debug_carriers():
    return jsonify([str(c) for c in Carrier.query.all()])


@app.route('/api/debug/shippers')
def debug_shippers():
    return jsonify([str(s) for s in Shipper.query.all()])
