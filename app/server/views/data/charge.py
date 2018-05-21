from logging import getLogger

import stripe
from flask import Blueprint
from settings import STRIPE_API_KEY

from app.server.helpers.api import ApiResponse, jsonify, parse_params


log = getLogger(__name__)


api_bp = Blueprint('charge_api', __name__)


@api_bp.route('/charge', methods=['POST'])
@jsonify
@parse_params(types=['json'])
def charge(json) -> ApiResponse:
    '''
    Stripe
    '''  # NOQA
    print("json:", json)

    # Set your secret key: remember to change this to your live secret key
    stripe.api_key = STRIPE_API_KEY

    # Token is created using Checkout or Elements!
    # Get the payment token ID submitted by the form:
    token = json.get('id')

    charge = stripe.Charge.create(
        amount=380,
        currency='jpy',
        description='作者に牛丼をおごる',
        source=token,
    )
    print("charge:", charge)
    return charge
