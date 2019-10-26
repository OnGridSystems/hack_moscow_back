import hashlib

from app import app, db
from app.models import Order, Shipper, Carrier, OrderStatus
from app.middlewares import session_middleware

from flask import request, jsonify, g
from uuid import uuid4


@app.after_request
def after_request_func(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response


@app.route('/api/register', methods=['POST'])
def register():
    request_body = request.json
    token = str(uuid4())
    print(f'register : {request_body}')

    role = request_body.get('role')
    username = request_body.get('username')
    password = request_body.get('password')
    address = request_body.get('location')

    if role not in ['SHIPPER', 'CARRIER']:
        return jsonify({'error': 'No role provided'}), 400
    if not username:
        return jsonify({'error': 'No username provided'}), 400
    if not password:
        return jsonify({'error': 'No password provided'}), 400
    if not address and role == 'SHIPPER':
        return jsonify({'error': 'No location provided'}), 400

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
                return jsonify({'error': 'No role provided'}), 400
            if not max_load:
                return jsonify({'error': 'No role provided'}), 400

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
            return jsonify({'error': e}), 500
        return jsonify({'token': token}), 200
    else:
        return jsonify({'error': 'Already registrated'}), 400


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
        return jsonify({'error': 'No such user'}), 404
    if user.password == password:
        return jsonify({'token': user.token}), 200


@app.route('/api/user')
@session_middleware
def user_info():
    user = g.user
    role = user.get_role()

    if role == 'SHIPPER':
        return (
            {
                'role': role,
                'username': user.username,
                'balance': user.balance,
                'location': user.address,
            },
            200,
        )
    elif role == 'CARRIER':
        return (
            {
                'role': role,
                'username': user.username,
                'balance': user.balance,
                'totalBalance': user.balance,
                'lockedBalance': user.locked,
                'availableBalance': user.balance - user.locked,
                'smartContract': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8',
                'vehicle': user.vehicle,
                'maxLoad': user.max_load,
            },
            200,
        )


@app.route('/api/available-orders')
@session_middleware
def available_orders():
    user = g.user
    if user.get_role() == 'SHIPPER':
        return jsonify({'error': 'you have no access'}), 401
    return (
        jsonify(
            [
                o.get_json(user.get_role())
                for o in Order.query.filter_by(status=OrderStatus.NOT_SENT)
            ]
        ),
        200,
    )


@app.route('/api/user/orders', methods=['POST', 'GET'])
@session_middleware
def user_orders():
    user = g.user
    if request.method == 'POST' and user.get_role() == 'SHIPPER':
        request_body = request.json

        # TODO: .get()
        pickup_location = request_body['pickupLocation']
        destination = request_body['destination']
        dimensions = request_body['dimensions']
        weight = request_body['weight']
        coverage = request_body['coverage']
        shipment_date = request_body['shipmentDate']
        delivery_date = request_body['deliveryDate']
        phone = request_body['phone']

        print(
            pickup_location,
            destination,
            dimensions,
            weight,
            coverage,
            shipment_date,
            delivery_date,
        )
        if (
            pickup_location
            and destination
            and dimensions
            and weight is not None
            and coverage is not None
            and shipment_date
            and delivery_date
            and phone
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
                phone=phone,
            )
            user.orders.append(o)
            db.session.add(o)
            db.session.add(user)
            db.session.commit()
            return jsonify({'info': 'Order created'}), 201
        else:
            return jsonify({'error': 'wrong request'}), 400
    elif request.method == 'GET':
        return jsonify([o.get_json(user.get_role()) for o in user.orders])
    else:
        return jsonify({'error': 'only shipper can create orders'}), 401


def get_distance(seed):
    return int(hashlib.sha1(seed.encode()).hexdigest()[:2], 16)


@app.route('/api/get-delivery-reward')
def get_delivery_reward():
    pickup_location = request.args.get('pickupLocation')
    destination = request.args.get('destination')

    if not destination and not pickup_location:
        return (
            jsonify({'error': 'no destination or pickupLocation provided'}),
            400,
        )

    seed = pickup_location + destination
    return {'reward': get_distance(seed) * 10}, 200


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

            return jsonify({'info': 'Order taken'}), 200
        else:
            return (
                jsonify({'error': 'your deposit is smaller then coverage'}),
                400,
            )
    else:
        return jsonify({'error': 'CARRIER role needed'}), 401


@app.route('/api/order-info')
def single_order_info():
    secret = request.args.get('orderSecret')
    if secret:
        o = Order.query.filter_by(secret=secret).first()
        return jsonify(o.get_json('SHIPPER')), 200
    else:
        return jsonify({'error': 'no such order'}), 404


@app.route('/api/confirm-delivery', methods=['POST'])
def confirm():
    request_body = request.json
    secret = request_body.get('orderSecret')
    if secret:
        o = Order.query.filter_by(secret=secret).first()
        o.status = OrderStatus.DELIVERED
        db.session.add(o)

        user = o.carrier
        user.locked -= o.coverage
        user.balance += o.reward
        db.session.add(user)

        db.session.commit()
        return jsonify({'info': 'Delivery confirmed'}), 200
    return jsonify({'error': 'no such order'}), 404


@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@session_middleware
def cancel(order_id):
    user = g.user
    if user.get_role() == 'SHIPPER':
        o = Order.query.filter_by(id=order_id).first()
        o.status = OrderStatus.CANCELLED
        db.session.add(o)
        db.session.commit()

        return jsonify({'info': 'order cancelled'}), 200
    return jsonify({'error': 'only SHIPPER role'}), 401


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
        db.session.add(user)
        db.session.commit()
    except Exception as e:  # TODO: change
        return jsonify({'error': e})
    return jsonify({'status': 200})


@app.route('/api/debug/carriers')
def debug_carriers():
    return jsonify([str(c) for c in Carrier.query.all()])


@app.route('/api/debug/shippers')
def debug_shippers():
    return jsonify([str(s) for s in Shipper.query.all()])
