from functools import wraps

from app.models import Shipper, Carrier

from flask import abort, g, request


def session_middleware(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        request_token = request.headers.get('Authorization')
        if request_token is None:
            abort(401)

        request_token = request_token[7:]
        user = Shipper.query.filter_by(token=request_token).first()
        if user:
            g.user = user
            return func(*args, **kwargs)

        user = Carrier.query.filter_by(token=request_token).first()
        if user:
            g.user = user
            return func(*args, **kwargs)

        abort(401)

    return decorator
