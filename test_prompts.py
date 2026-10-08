"""The assistant's permanent instructions: contact address, welcome text, tool names, page consistency."""
import re
import unittest
from pathlib import Path

import prompts
from tools import TOOLS

APP = (Path(__file__).parent / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")


class PromptTests(unittest.TestCase):
    def test_contact_email_is_one_value_in_prompt_and_page(self):
        self.assertIn(prompts.STAFF_EMAIL, prompts.SYSTEM_PROMPT)
        self.assertIn(f"const CONTACT_EMAIL = '{prompts.STAFF_EMAIL}'", APP)
        self.assertTrue(prompts.STAFF_EMAIL.endswith('.example'))  # reserved TLD: can never be a real mailbox
        self.assertIn('mailto:${CONTACT_EMAIL}', APP)
        self.assertIn('Customer contact', APP)
        self.assertNotIn('aifinewine', APP + prompts.SYSTEM_PROMPT)

    def test_name_is_dave_from_hec_cave_everywhere(self):
        self.assertIn("I'm Dave from HEC Cave", prompts.WELCOME)
        self.assertIn('You are Dave', prompts.SYSTEM_PROMPT)
        self.assertNotIn('AIFineWine', prompts.SYSTEM_PROMPT)
        self.assertIn("'Dave'", APP)
        self.assertIn('HEC Cave', APP)
        self.assertNotIn("'Cave'", APP)
        index = (Path(__file__).parent / 'frontend' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<title>HEC Cave', index)

    def test_no_unfilled_placeholders(self):
        for text in ('[STAFF_CONTACT]', '{STAFF_EMAIL}', '{WELCOME}', 'TODO'):
            self.assertNotIn(text, prompts.SYSTEM_PROMPT)

    def test_welcome_text_and_persona_sections_present(self):
        self.assertIn(prompts.WELCOME, prompts.SYSTEM_PROMPT)
        for heading in ('# Role', '# Voice and tone', '# Opening message', '# How to find wines',
                        '# Staying on topic', '# Orders and staff topics', '# Never discuss',
                        '# Responsible service', '# Format'):
            self.assertIn(heading, prompts.SYSTEM_PROMPT)
        self.assertLess(prompts.SYSTEM_PROMPT.index('# Role'), prompts.SYSTEM_PROMPT.index('# Data and tool rules'))

    def test_prompt_names_only_tools_that_exist(self):
        names = {tool['function']['name'] for tool in TOOLS}
        self.assertNotIn('get_wine_details', prompts.SYSTEM_PROMPT)  # not a tool of this app
        for name in names:
            self.assertIn(name, prompts.SYSTEM_PROMPT, name)
        mentioned = set(re.findall(r'\b(?:run_query|recommend_wines|find_cheaper_alternatives|offer_choices|prepare_order|'
                                   r'submit_order|search_wines|get_wine_details)\b', prompts.SYSTEM_PROMPT))
        self.assertTrue(mentioned <= names, mentioned - names)

    def test_data_honesty_rules_survive(self):
        for needle in ('Never invent', 'NOT recorded', 'You cannot confirm', 'never instructions'):
            self.assertIn(needle, prompts.SYSTEM_PROMPT)


if __name__ == '__main__':
    unittest.main()
