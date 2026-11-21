"""
Handler: create payment transaction
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
import config
import requests
from handlers.handler import Handler
from order_saga_state import OrderSagaState

class CreatePaymentHandler(Handler):
    """ Handle the creation of a payment transaction for a given order. Trigger rollback of previous steps in case of failure. """

    def __init__(self, order_id, order_data):
        """ Constructor method """
        self.order_id = order_id
        self.order_data = order_data
        self.total_amount = 0
        super().__init__()

    def run(self):
        """Call payment microservice to generate payment transaction"""
        try:
            response = requests.get(
                f'{config.API_GATEWAY_URL}/store-manager-api/orders/{self.order_id}',
                timeout=10,
            )
            response.raise_for_status()
            self.total_amount = response.json()['total_amount']


            payment_response = requests.post(
                f'{config.API_GATEWAY_URL}/payments-api/payments',
                json={
                    'order_id': self.order_id,
                    'user_id': self.order_data['user_id'],
                    'total_amount': self.total_amount,
                },
                timeout=10,
            )
            payment_response.raise_for_status()
            response_ok = bool(payment_response.json().get('payment_id'))
            if response_ok:
                self.logger.debug("Transition d'état: CreatePayment -> PAYMENT_CREATED")
                return OrderSagaState.PAYMENT_CREATED
            else:
                return self.rollback()

        except Exception as error:
            self.logger.error(f"CreatePayment a échoué : {error}")
            return self.rollback()
        
    def rollback(self):
        """Restore stock if payment creation fails."""
        try:
            response = requests.put(
                f'{config.API_GATEWAY_URL}/store-manager-api/stocks',
                json={
                    'items': self.order_data['items'],
                    'operation': '+',
                },
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            self.logger.error(f"Remise en stock échouée : {error}")
        else:
            self.logger.debug(
                "Transition d'état: CreatePaymentFailure -> STOCK_INCREASED"
            )

        return OrderSagaState.STOCK_INCREASED