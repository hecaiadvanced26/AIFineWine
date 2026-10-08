"""Test catalog migration and rich preference SQL using a temporary database."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import refresh_demo_catalog
from catalog import run_query


class CatalogTests(unittest.TestCase):
    def test_runtime_directory_seeds_from_bundled_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder) / 'runtime' / 'data'
            with patch.object(database, 'DATA_DIR', data), \
                    patch.object(database, 'DB_PATH', data / 'wines.db'):
                database.initialize()
                db = database.connect()
                try:
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM wines').fetchone()[0], 200)
                    with db:
                        db.execute("UPDATE wines SET stock=1 WHERE wine_id='W-001'")
                    database.initialize()
                    self.assertEqual(db.execute(
                        "SELECT stock FROM wines WHERE wine_id='W-001'").fetchone()[0], 1)
                finally:
                    db.close()

    def test_refresh_preserves_stock_orders_and_backs_up(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            shutil.copy(database.DATA_DIR / 'demo_wines.json', data / 'demo_wines.json')
            with patch.object(database, 'DATA_DIR', data), patch.object(database, 'DB_PATH', data / 'wines.db'), \
                    patch.object(refresh_demo_catalog, 'DATA_DIR', data):
                database.initialize()
                db = database.connect()
                with db:
                    db.execute("UPDATE wines SET name='Demo wine A', stock=4 WHERE wine_id='W-001'")
                    db.execute("INSERT INTO orders VALUES ('old-order', '{}')")
                db.close()
                backup = refresh_demo_catalog.refresh_catalog()
                self.assertTrue(backup.exists())
                db = database.connect()
                self.assertEqual(db.execute("SELECT stock FROM wines WHERE wine_id='W-001'").fetchone()[0], 4)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0], 1)
                db.close()
                result = run_query("""SELECT wine_id FROM wines WHERE stock > 0
                    AND json_extract(attributes, '$.type') = 'red'
                    AND json_extract(attributes, '$.country') = 'Italy'
                    AND EXISTS (SELECT 1 FROM json_each(wines.attributes, '$.taste')
                    WHERE value = 'cherry') ORDER BY wine_id""")
                self.assertEqual(result['status'], 'ok')
                self.assertTrue(result['rows'])

    def test_refresh_adds_missing_wines_without_touching_existing_stock(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            shutil.copy(database.DATA_DIR / 'demo_wines.json', data / 'demo_wines.json')
            with patch.object(database, 'DATA_DIR', data), patch.object(database, 'DB_PATH', data / 'wines.db'), \
                    patch.object(refresh_demo_catalog, 'DATA_DIR', data):
                database.initialize()
                db = database.connect()
                with db:
                    db.execute("DELETE FROM wines WHERE wine_id='W-002'")
                    db.execute("UPDATE wines SET stock=3 WHERE wine_id='W-001'")
                db.close()
                refresh_demo_catalog.refresh_catalog()
                db = database.connect()
                self.assertEqual(db.execute('SELECT COUNT(*) FROM wines').fetchone()[0], 200)
                self.assertEqual(db.execute("SELECT stock FROM wines WHERE wine_id='W-001'").fetchone()[0], 3)
                db.close()


class CatalogDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads((database.DATA_DIR / 'demo_wines.json').read_text(encoding='utf-8'))
        from prompts import ATTRIBUTE_DESCRIPTIONS
        m = re.search(r'closed list of 88\): (.+?)\.\n', ATTRIBUTE_DESCRIPTIONS)
        cls.prompt_tags = set(m.group(1).split(', ')) if m else set()

    def test_ids_unique_and_count(self):
        ids = [r['wine_id'] for r in self.rows]
        self.assertEqual(len(ids), 200)
        self.assertEqual(len(set(ids)), 200)

    def test_prompt_lists_88_tags_and_data_uses_only_those(self):
        self.assertEqual(len(self.prompt_tags), 88)
        for r in self.rows:
            for key in ('taste', 'taste_style_guess'):
                self.assertLessEqual(set(r['attributes'][key]), self.prompt_tags, r['wine_id'])

    def test_no_contact_data_in_catalog(self):
        text = json.dumps(self.rows, ensure_ascii=False)
        self.assertNotRegex(text, r'[\w.+-]+@[\w-]+\.[\w.]+|https?://|www\.')

    def test_no_missing_name_prefix_and_valid_numbers(self):
        for r in self.rows:
            self.assertFalse(r['name'].startswith('None'), r['wine_id'])
            self.assertIsInstance(r['price_cents'], int)
            self.assertGreaterEqual(r['stock'], 0)


if __name__ == '__main__':
    unittest.main()
