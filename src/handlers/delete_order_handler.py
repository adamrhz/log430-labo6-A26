"""
Handler: delete order
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
import config
import requests
from handlers.handler import Handler
from order_saga_state import OrderSagaState

class DeleteOrderHandler(Handler):
    """ Handle order deletion. """

    def __init__(self, order_id):
        """ Constructor method """
        self.order_id = order_id
        super().__init__()

    def run(self):
        """Supprimer la commande si la saga échoue."""
        try:
            response = requests.delete(
                f'{config.API_GATEWAY_URL}/store-manager-api/orders/{self.order_id}',
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            self.logger.error(f"Suppression de la commande {self.order_id} échouée : {error}")
            return OrderSagaState.END

        self.logger.debug("Transition d'état: DeleteOrder -> ORDER_DELETED")
        return OrderSagaState.ORDER_DELETED
        
    def rollback(self):
        """
        (rollback not applicable for DeleteOrder)
        """
        # Nous héritons de la classe abstraite Handler, et par conséquent, l'implémentation de la méthode rollback() est obligatoire.
        pass
