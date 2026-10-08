"""Changing the quantity of an order draft: server-side limits, new draft, stock untouched."""
import unittest

import database
import orders
import server
from test_advisor import DbCase


class QuantityTests(DbCase):
    def setUp(self):
        super().setUp()
        server.conversations.clear()
        self.client = server.app.test_client()
        self.client.post('/api/reset', json={})
        with self.client.session_transaction() as session:
            self.memory = server.conversations[session['chat_id']]['memory']
        db = database.connect()
        try:
            self.wine_id, self.stock, self.price = db.execute(
                "SELECT wine_id, stock, price_cents FROM wines WHERE stock >= 5 ORDER BY wine_id").fetchone()[:3]
        finally:
            db.close()
        self.memory.pending_order = orders.prepare_order(self.wine_id, 1)

    def stock_now(self):
        db = database.connect()
        try:
            return db.execute("SELECT stock FROM wines WHERE wine_id=?", (self.wine_id,)).fetchone()[0]
        finally:
            db.close()

    def post(self, quantity, order_id=None):
        return self.client.post('/api/order', json={'action': 'quantity', 'quantity': quantity,
                                                    'order_id': order_id or self.memory.pending_order['order_id']})

    def test_draft_carries_max_quantity(self):
        self.assertEqual(self.memory.pending_order['max_quantity'], self.stock)

    def test_valid_change_creates_new_draft_with_server_prices(self):
        old = self.memory.pending_order['order_id']
        response = self.post(3)
        self.assertEqual(response.status_code, 200)
        draft = response.get_json()['draft']
        self.assertEqual(draft['quantity'], 3)
        self.assertEqual(draft['total_cents'], 3 * self.price)
        self.assertNotEqual(draft['order_id'], old)
        self.assertEqual(self.memory.pending_order, draft)
        self.assertEqual(self.stock_now(), self.stock)  # nothing reserved or sold yet
        self.assertEqual(self.post(2, order_id=old).status_code, 409)  # the old draft is dead

    def test_maximum_is_the_stock_and_one_more_is_refused(self):
        self.assertEqual(self.post(self.stock).status_code, 200)
        before = self.memory.pending_order
        response = self.post(self.stock + 1)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.memory.pending_order, before)
        self.assertEqual(response.get_json()['draft']['quantity'], self.stock)

    def test_bad_quantities_refused_and_draft_kept(self):
        before = self.memory.pending_order
        for bad in (0, -2, 2.5, '3', None, True, 10 ** 9):
            self.assertEqual(self.post(bad).status_code, 400, repr(bad))
        self.assertEqual(self.memory.pending_order, before)

    def test_wrong_order_id_or_no_draft(self):
        self.assertEqual(self.post(2, order_id='nope').status_code, 409)
        self.memory.pending_order = None
        self.assertEqual(self.client.post('/api/order', json={'action': 'quantity', 'quantity': 2,
                                                              'order_id': 'x'}).status_code, 409)

    def test_confirm_after_change_exports_the_new_quantity_and_reduces_stock(self):
        self.post(2)
        response = self.client.post('/api/order', json={'action': 'confirm',
                                                        'order_id': self.memory.pending_order['order_id']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['confirmation']['quantity'], 2)
        self.assertEqual(self.stock_now(), self.stock - 2)


if __name__ == '__main__':
    unittest.main()
