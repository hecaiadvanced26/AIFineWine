"""Catalog import, migration, provenance search and order regression checks."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import orders
import refresh_demo_catalog
from catalog import get_wine_details, run_query

WINE_ID = 'W-010'  # stock 2 in the fictional catalogue


_CATALOG = json.loads((database.SOURCE_DATA_DIR / 'catalog.json').read_text(encoding='utf-8'))['wines']
CATALOG_NAMES = {w['wine_id']: w['name'] for w in _CATALOG}
CATALOG_PRICES = {w['wine_id']: w['price_cents'] for w in _CATALOG}
CATALOG_VINTAGES = {w['wine_id']: w['vintage'] for w in _CATALOG}
UNNOTED_ID = next(w['wine_id'] for w in _CATALOG if w['stock'] > 0
                  and not any(f['provenance'] == 'stated' for f in w['flavours']))


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.data = Path(self.folder.name) / 'runtime' / 'data'
        for target, name, value in [(database, 'DATA_DIR', self.data),
                                    (database, 'DB_PATH', self.data / 'wines.db'),
                                    (orders, 'DATA_DIR', self.data),
                                    (refresh_demo_catalog, 'DATA_DIR', self.data)]:
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_seed_counts_provenance_and_idempotent_startup(self):
        database.initialize()
        db = database.connect()
        self.addCleanup(db.close)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM wines').fetchone()[0], 250)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM flavours').fetchone()[0], 1028)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM flavour_vocabulary').fetchone()[0], 88)
        counts = {row[0]: row[1] for row in db.execute(
            'SELECT provenance,COUNT(*) FROM flavours GROUP BY provenance')}
        self.assertEqual(counts, {'guess': 828, 'stated': 200})
        with db:
            db.execute('UPDATE wines SET stock=1 WHERE wine_id=?', (WINE_ID,))
        database.initialize()
        self.assertEqual(db.execute('SELECT stock FROM wines WHERE wine_id=?', (WINE_ID,)).fetchone()[0], 1)

    def test_legacy_migration_backup_and_order_history(self):
        self.data.mkdir(parents=True)
        db = sqlite3.connect(database.DB_PATH)
        db.executescript("""CREATE TABLE wines (wine_id TEXT PRIMARY KEY, name TEXT NOT NULL,
            price_cents INTEGER NOT NULL, vintage INTEGER, stock INTEGER NOT NULL, attributes TEXT NOT NULL);
            CREATE TABLE orders (order_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            INSERT INTO wines VALUES ('DEMO-001','Old demo',995,2023,4,'{}');
            INSERT INTO orders VALUES ('old-order','{"wine_id":"DEMO-001"}');""")
        db.close()
        backup = refresh_demo_catalog.refresh_catalog()
        self.assertTrue(backup.exists())
        with sqlite3.connect(backup) as old:
            self.assertEqual(old.execute('SELECT wine_id FROM wines').fetchone()[0], 'DEMO-001')
        db = database.connect()
        self.addCleanup(db.close)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM wines').fetchone()[0], 250)
        self.assertEqual(json.loads(db.execute('SELECT payload FROM orders').fetchone()[0])['wine_id'], 'DEMO-001')

    def test_refresh_preserves_existing_stock(self):
        database.initialize()
        db = database.connect()
        self.addCleanup(db.close)
        with db:
            db.execute('UPDATE wines SET name=?, stock=1 WHERE wine_id=?', ('Old metadata', WINE_ID))
        refresh_demo_catalog.refresh_catalog()
        row = db.execute('SELECT name,stock FROM wines WHERE wine_id=?', (WINE_ID,)).fetchone()
        self.assertEqual(row['stock'], 1)
        self.assertEqual(row['name'], CATALOG_NAMES[WINE_ID])

    def test_stated_flavour_search_excludes_style_guesses(self):
        database.initialize()
        result = run_query("""SELECT wine_id FROM wines w WHERE stock>0 AND EXISTS
            (SELECT 1 FROM flavours f WHERE f.wine_id=w.wine_id
             AND f.tag='blackberry' AND f.provenance='stated') ORDER BY wine_id LIMIT 5""")
        self.assertEqual(result['status'], 'ok')
        self.assertIn({'wine_id': 'W-057'}, result['rows'])
        details = get_wine_details(UNNOTED_ID)
        self.assertTrue(details['flavours'])
        self.assertTrue(all(flavour['provenance'] == 'guess' for flavour in details['flavours']))
        self.assertEqual(details['inventory_synthetic'], 1)

    def test_order_price_stock_and_duplicate_confirmation(self):
        database.initialize()
        draft = orders.prepare_order(WINE_ID, 2)
        self.assertEqual(draft['total_cents'], 2 * CATALOG_PRICES[WINE_ID])
        self.assertEqual(draft['vintage'], CATALOG_VINTAGES[WINE_ID])
        first = orders.submit_order(draft)
        self.assertNotIn('error', first)
        self.assertEqual(orders.submit_order(draft)['order_id'], first['order_id'])
        self.assertEqual(get_wine_details(WINE_ID)['stock'], 0)
        self.assertIn('error', orders.prepare_order(WINE_ID, 1))
        self.assertTrue(Path(first['file']).exists())

    def test_failed_import_rolls_back_entire_catalog(self):
        database.initialize()
        snapshot = database.load_catalog()
        snapshot['wines'][0]['flavours'].append({'tag': 'not-in-vocabulary', 'provenance': 'stated'})
        with patch.object(refresh_demo_catalog, 'load_catalog', return_value=snapshot):
            with self.assertRaises(sqlite3.IntegrityError):
                refresh_demo_catalog.refresh_catalog()
        db = database.connect()
        self.addCleanup(db.close)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM wines').fetchone()[0], 250)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM flavours').fetchone()[0], 1028)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM flavour_vocabulary').fetchone()[0], 88)

    def test_changed_price_requires_new_draft(self):
        database.initialize()
        draft = orders.prepare_order(WINE_ID, 1)
        db = database.connect()
        self.addCleanup(db.close)
        with db:
            db.execute('UPDATE wines SET price_cents=1200 WHERE wine_id=?', (WINE_ID,))
        self.assertIn('error', orders.submit_order(draft))
        self.assertEqual(get_wine_details(WINE_ID)['stock'], 2)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0], 0)



class ShortIdTests(unittest.TestCase):
    def test_ids_are_short_and_unique(self):
        import re
        snapshot = json.loads((database.SOURCE_DATA_DIR / 'catalog.json').read_text(encoding='utf-8'))
        ids = [w['wine_id'] for w in snapshot['wines']]
        self.assertEqual(len(ids), 250)
        self.assertEqual(len(set(ids)), 250)
        self.assertTrue(all(re.fullmatch(r'W-\d{3}', i) for i in ids))


if __name__ == '__main__':
    unittest.main()
