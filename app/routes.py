from app import app, db
from app.models import Order, Shipper, Carrier
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
    if not address:
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
                address=address,
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
            'location': user.address,
            'totalBalance': user.balance,
            'lockedBalance': user.locked,
            'availableBalance': user.balance - user.locked,
            'smartContract': '0xDJKJKDr6yDS7aDdfghjk234567sdfghj',
            'vehicle': user.vehicle,
            'maxLoad': user.max_load,
        }


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
