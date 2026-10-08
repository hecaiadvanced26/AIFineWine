"""Guided-advice tools against the real 200-wine catalog in a temporary database."""
import json
import tempfile
import xml.etree.ElementTree as ET
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import orders
import tools
from advisor import find_cheaper_alternatives, fit_score, offer_choices, recommend_wines
from memory import Memory

ARGS = dict(wine_type="any", budget_min_eur=None, budget_max_eur=None, aroma_families=[],
            aromas=[], country=None, include_style_guesses=False)


class DbCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        data = Path(folder.name) / 'data'
        for target, name, value in ((database, 'DATA_DIR', data), (database, 'DB_PATH', data / 'wines.db'),
                                    (orders, 'DATA_DIR', data)):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        database.initialize()


class AdvisorTests(DbCase):
    def rec(self, **kw):
        return recommend_wines(**{**ARGS, **kw})

    def test_hard_filters_and_limit(self):
        result = self.rec(wine_type='red', budget_max_eur=12)
        self.assertEqual(result['status'], 'ok')
        self.assertLessEqual(len(result['wines']), 3)
        for wine in result['wines']:
            self.assertEqual(wine['wine_type'], 'red')
            self.assertLessEqual(wine['price_eur'], 12)
            self.assertGreater(wine['stock'], 0)
        json.dumps(result)

    def test_aroma_wish_uses_stated_only_unless_allowed(self):
        strict = self.rec(wine_type='red', aroma_families=['Red-wine fruit'])
        for wine in strict['wines']:
            self.assertTrue(any('Red-wine fruit (taster-stated)' in m for m in wine['matched']), wine['wine_id'])
        loose = self.rec(wine_type='white', aroma_families=['Floral'], include_style_guesses=True)
        kinds = {m for w in loose['wines'] for m in w['matched'] if 'Floral' in m}
        self.assertTrue(kinds)

    def test_strict_mode_never_counts_style_guesses(self):
        for family in ('Red-wine fruit', 'White-wine fruit', 'Floral', 'Mineral', 'Oak ageing'):
            result = self.rec(aroma_families=[family])
            for wine in result['wines']:
                self.assertFalse(any('style guess' in m for m in wine['matched']), (family, wine['wine_id']))

    def test_unmet_wishes_are_reported_not_hidden(self):
        result = self.rec(wine_type='red', aromas=['truffle'], country='Italy')
        for wine in result['wines']:
            self.assertEqual(wine['wishes_met'], len(wine['matched']))
            self.assertEqual(wine['wishes_met'] + len(wine['not_matched']), wine['wishes_total'])
        self.assertIn('style_guess_hint', result)

    def test_ranking_is_by_wishes_met(self):
        met = [w['wishes_met'] for w in self.rec(wine_type='red', aroma_families=['Red-wine fruit'],
                                                   country='Italy')['wines']]
        self.assertEqual(met, sorted(met, reverse=True))

    def test_fit_score_is_share_of_wishes_met_on_a_1_to_5_scale(self):
        self.assertEqual([fit_score(m, 3) for m in (0, 1, 2, 3)], [1, 2, 3, 5])
        self.assertEqual(fit_score(4, 4), 5)
        self.assertEqual(fit_score(1, 5), 1)
        self.assertIsNone(fit_score(0, 0))
        result = self.rec(wine_type='red', budget_max_eur=12, aroma_families=['Red-wine fruit'], country='Italy')
        for wine in result['wines']:
            self.assertEqual(wine['fit_score'], fit_score(wine['wishes_met'], wine['wishes_total']))
            self.assertIn(wine['fit_score'], (1, 2, 3, 4, 5))
        self.assertIsNone(self.rec()['wines'][0]['fit_score'])

    def test_no_match_says_so(self):
        result = self.rec(wine_type='red', budget_max_eur=1)
        self.assertEqual(result['status'], 'no_matches')
        self.assertEqual(result['wines'], [])

    def test_bad_input_rejected(self):
        for bad in ({'wine_type': 'purple'}, {'budget_max_eur': -3}, {'budget_min_eur': 9, 'budget_max_eur': 5},
                    {'aroma_families': ['Faults']}, {'aromas': ['unicorn']}, {'include_style_guesses': 'yes'}):
            with self.assertRaises(ValueError, msg=str(bad)):
                self.rec(**bad)

    def test_cheaper_alternatives_are_cheaper_same_colour_with_shared_aromas(self):
        db = database.connect()
        try:
            candidates = [r[0] for r in db.execute("SELECT wine_id FROM wines WHERE price_cents >= 1500 AND stock > 0")]
        finally:
            db.close()
        checked = 0
        for wine_id in candidates:
            result = find_cheaper_alternatives(wine_id)
            for alt in result.get('alternatives', []):
                checked += 1
                self.assertLess(alt['price_eur'], result['chosen']['price_eur'])
                self.assertEqual(alt['wine_type'], result['chosen']['wine_type'])
                self.assertGreater(alt['stock'], 0)
                self.assertTrue(alt['shared_aromas'] or alt['shared_grapes'])
                self.assertIsNone(alt['fit_score'])
                self.assertAlmostEqual(alt['price_difference_eur'],
                                       result['chosen']['price_eur'] - alt['price_eur'], places=2)
        self.assertGreater(checked, 0)
        self.assertEqual(find_cheaper_alternatives('nope'), {'error': 'Unknown wine ID.'})

    def test_offer_choices_validation(self):
        self.assertEqual(offer_choices(['Red', 'White'], 1, 3)['step'], 1)
        for args in ((['one'], 1, 3), (['a', 'b'], 0, 3), (['a', 'b'], 4, 3), (['a', ''], 1, 3),
                     (['a', 'b'], True, 3), ('ab', 1, 3)):
            with self.assertRaises(ValueError, msg=str(args)):
                offer_choices(*args)

    def test_dispatch_stores_ui_payloads_and_rejects_bad_arguments(self):
        memory = Memory()
        out = tools.dispatch('recommend_wines', json.dumps({**ARGS, 'wine_type': 'white'}), memory)
        self.assertEqual(out['status'], 'ok')
        self.assertEqual(memory.recommendations['wines'], out['wines'])
        memory.reset_cards()  # one output per turn: chips only in a turn without cards
        tools.dispatch('offer_choices', json.dumps({'options': ['Red', 'White'], 'step': 1, 'total': 3}), memory)
        self.assertEqual(memory.choices['options'], ['Red', 'White'])
        bad = tools.dispatch('recommend_wines', json.dumps({**ARGS, 'wine_type': 'blue'}), Memory())
        self.assertEqual(bad['status'], 'invalid_arguments')
        memory.reset_cards()
        self.assertIsNone(memory.recommendations)
        self.assertIsNone(memory.choices)


class WineImageTests(DbCase):
    def setUp(self):
        super().setUp()
        import server
        self.client = server.app.test_client()

    def test_every_wine_gets_valid_svg_without_invented_nv(self):
        db = database.connect()
        try:
            ids = [r[0] for r in db.execute('SELECT wine_id FROM wines')]
            missing_vintage = db.execute('SELECT wine_id FROM wines WHERE vintage IS NULL LIMIT 1').fetchone()[0]
        finally:
            db.close()
        self.assertEqual(len(ids), 250)
        for wine_id in ids:
            response = self.client.get(f'/api/wine-image/{wine_id}.svg')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/svg+xml')
            ET.fromstring(response.data)
        body = self.client.get(f'/api/wine-image/{missing_vintage}.svg').get_data(as_text=True)
        self.assertNotIn('>NV<', body)

    def test_unknown_id_gets_placeholder_and_text_is_escaped(self):
        response = self.client.get('/api/wine-image/does-not-exist.svg')
        self.assertEqual(response.status_code, 200)
        ET.fromstring(response.data)
        from make_wine_images import bottle_svg
        svg = bottle_svg('<script>alert(1)</script> & "x"', '<b>', 2020, 'red')
        self.assertNotIn('<script>', svg)
        ET.fromstring(svg)


if __name__ == '__main__':
    unittest.main()
