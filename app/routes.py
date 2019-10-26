from app import app, db
from app.models import Order, Shipper, Carrier
from app.middlewares import session_middleware

from flask import request, jsonify, g
from uuid import uuid4


@app.route('/api/user/register', methods=['POST'])
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
        if role == 'Shipper':
            u = Shipper(
                username=username,
                password=password,
                token=token,
                address=address,
            )
        elif role == 'Carrier':
            u = Carrier(
                username=username,
                password=password,
                token=token,
                address=address,
            )

        try:
            db.session.add(u)
            db.session.commit()
        except Exception as e: # TODO: change
            return jsonify({'error': e})
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Already registrated'})


@app.route('/api/user/login', methods=['POST'])
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


@app.route('/api/debug/carriers')
def debug_carriers():
    return jsonify([str(c) for c in Carrier.query.all()])

@app.route('/api/debug/shippers')
def debug_shippers():
    return jsonify([str(s) for s in Shipper.query.all()])