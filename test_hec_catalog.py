"""Checks for the fictional 250-wine cave. catalogue and the profile/pairing filters."""
import collections
import json
import re
import unittest

import database
from advisor import find_cheaper_alternatives, recommend_wines
from test_advisor import ARGS, DbCase

CATALOG = json.loads((database.SOURCE_DATA_DIR / 'catalog.json').read_text(encoding='utf-8'))
WINES = CATALOG['wines']


class CatalogDataTests(unittest.TestCase):
    def test_size_colours_and_diversity(self):
        self.assertEqual(len(WINES), 250)
        self.assertEqual({w['wine_type'] for w in WINES}, {'red', 'white', 'rose', 'sparkling'})
        self.assertGreaterEqual(len({w['country'] for w in WINES}), 8)
        self.assertGreaterEqual(len({w['appellation'] for w in WINES}), 40)
        self.assertEqual(len({w['name'] + str(w['vintage']) for w in WINES}), 250)

    def test_same_cuvee_three_vintages_differ_in_price_and_rating(self):
        groups = collections.defaultdict(list)
        for w in WINES:
            groups[(w['winery'], w['name'])].append(w)
        triplets = [v for v in groups.values() if len(v) == 3]
        self.assertGreaterEqual(len(triplets), 9)
        for group in triplets:
            self.assertEqual(len({w['vintage'] for w in group}), 3)
            self.assertEqual(len({w['price_cents'] for w in group}), 3, group[0]['name'])
            self.assertEqual(len({w['community_avg_rating'] for w in group}), 3, group[0]['name'])

    def test_exactly_75_noted_wines_and_notes_match_stated_aromas(self):
        noted = [w for w in WINES if w['user_review']]
        self.assertEqual(len(noted), 75)
        for w in noted:
            stated = {f['tag'] for f in w['flavours'] if f['provenance'] == 'stated'}
            self.assertTrue(stated, w['wine_id'])
            for tag in stated:
                self.assertRegex(w['user_review'].lower(), r'\b' + re.escape(tag.lower()), (w['wine_id'], tag))
        for w in WINES:
            if not w['user_review']:
                self.assertFalse([f for f in w['flavours'] if f['provenance'] == 'stated'], w['wine_id'])

    def test_profiles_are_in_scale_and_tannin_only_for_reds(self):
        for w in WINES:
            for key in ('sweetness', 'body', 'acidity', 'fruitiness'):
                self.assertIn(w[key], (1, 2, 3, 4, 5), (w['wine_id'], key))
            if w['wine_type'] == 'red':
                self.assertIn(w['tannin'], (1, 2, 3, 4, 5))
            else:
                self.assertIsNone(w['tannin'], w['wine_id'])
            self.assertTrue(w['pairings'], w['wine_id'])


class FilterTests(DbCase):
    def rec(self, **kw):
        return recommend_wines(**{**ARGS, **kw})

    def test_structure_wishes_rank_matching_wines_first(self):
        result = self.rec(wine_type='red', tannin='high', body='full')
        self.assertTrue(result['wines'])
        for w in result['wines']:
            self.assertEqual(w['profile']['tannin'], 'high')
            self.assertEqual(w['profile']['body'], 'full')
            self.assertEqual(w['fit_score'], 5)

    def test_food_filter_returns_wines_listing_that_food(self):
        result = self.rec(foods=['risotto'])
        self.assertTrue(result['wines'])
        for w in result['wines']:
            self.assertIn('risotto', w['food_pairings'])

    def test_grape_filter_accepts_shiraz_alias(self):
        result = self.rec(wine_type='red', grapes=['Shiraz'])
        self.assertTrue(result['wines'])
        for w in result['wines']:
            self.assertIn('Syrah', w['grapes'])

    def test_sweet_wines_exist_and_are_found(self):
        result = self.rec(sweetness='sweet')
        self.assertTrue(result['wines'])
        self.assertEqual(result['wines'][0]['profile']['sweetness'], 'sweet')

    def test_vintages_of_one_cuvee_are_distinguishable_in_results(self):
        groups = collections.defaultdict(list)
        for w in WINES:
            groups[(w['winery'], w['name'])].append(w)
        group = next(v for v in groups.values() if len(v) == 3 and all(w['stock'] > 0 for w in v))
        for w in group:
            alt = find_cheaper_alternatives(w['wine_id'])
            self.assertEqual(alt['chosen']['price_eur'], w['price_cents'] / 100)
            self.assertEqual(alt['chosen']['vintage'], w['vintage'])


class OneOutputPerTurnTests(DbCase):
    def call(self, memory, name, **args):
        import tools
        return tools.dispatch(name, json.dumps(args), memory)

    def test_cards_then_alternatives_or_question_are_blocked(self):
        from memory import Memory
        memory = Memory()
        shown = self.call(memory, 'recommend_wines', **{**ARGS, 'foods': ['risotto']})
        self.assertTrue(shown['wines'])
        wine_id = shown['wines'][0]['wine_id']
        for name, args in (('find_cheaper_alternatives', {'wine_id': wine_id}),
                           ('offer_choices', {'options': ['Red', 'White'], 'step': 1, 'total': 3})):
            self.assertEqual(self.call(memory, name, **args)['status'], 'blocked', name)
        self.assertIsNone(memory.comparison)
        self.assertIsNone(memory.choices)
        self.assertEqual(len(memory.recommendations['wines']), 3)

    def test_question_then_cards_is_blocked(self):
        from memory import Memory
        memory = Memory()
        self.assertEqual(self.call(memory, 'offer_choices', options=['Red', 'White'], step=1, total=3)['status'], 'shown')
        self.assertEqual(self.call(memory, 'recommend_wines', **ARGS)['status'], 'blocked')
        self.assertIsNone(memory.recommendations)

    def test_alternatives_alone_still_work_and_block_a_second_set(self):
        from memory import Memory
        memory = Memory()
        wine_id = next(w['wine_id'] for w in WINES if w['stock'] > 0 and w['price_cents'] >= 3000)
        self.call(memory, 'find_cheaper_alternatives', wine_id=wine_id)
        self.assertTrue(memory.comparison)
        self.assertEqual(self.call(memory, 'recommend_wines', **ARGS)['status'], 'blocked')

    def test_game_tag_is_game_meat(self):
        foods = {f['food'] for f in CATALOG['food_vocabulary']}
        self.assertIn('game meat', foods)
        self.assertNotIn('game', foods)
        self.assertTrue(self.call(__import__('memory').Memory(), 'recommend_wines', **{**ARGS, 'foods': ['game meat']})['wines'])


if __name__ == '__main__':
    unittest.main()
