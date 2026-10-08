"""Test catalog migration and rich preference SQL using a temporary database."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import refresh_demo_catalog
from catalog import run_query


class CatalogTests(unittest.TestCase):
    def test_refresh_preserves_stock_orders_and_backs_up(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            shutil.copy(database.DATA_DIR / 'demo_wines.json', data / 'demo_wines.json')
            with patch.object(database, 'DATA_DIR', data), patch.object(database, 'DB_PATH', data / 'wines.db'), \
                    patch.object(refresh_demo_catalog, 'DATA_DIR', data):
                database.initialize()
                db = database.connect()
                with db:
                    db.execute("UPDATE wines SET name='Demo wine A', stock=4 WHERE wine_id='DEMO-001'")
                    db.execute("INSERT INTO orders VALUES ('old-order', '{}')")
                db.close()
                backup = refresh_demo_catalog.refresh_catalog()
                self.assertTrue(backup.exists())
                db = database.connect()
                self.assertEqual(db.execute("SELECT stock FROM wines WHERE wine_id='DEMO-001'").fetchone()[0], 4)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0], 1)
                db.close()
                result = run_query("""SELECT wine_id FROM wines WHERE stock > 0
                    AND json_extract(attributes, '$.type') = 'red'
                    AND json_extract(attributes, '$.country') = 'Spain'
                    AND json_extract(attributes, '$.fruity') = 1
                    AND json_extract(attributes, '$.sweetness') = 'dry'
                    AND EXISTS (SELECT 1 FROM json_each(wines.attributes, '$.pairings')
                    WHERE value = 'chicken')""")
                self.assertEqual(result['rows'], [{'wine_id': 'DEMO-001'}])


if __name__ == '__main__':
    unittest.main()
