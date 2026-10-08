# Failure log (honest, short)

How to read: *Seen by* tells who found it and how. *Status* says what was actually verified. "Offline" means unit
tests with a stand-in model; nothing here has yet been confirmed with the real model unless it says so.

| # | What went wrong | Seen by | Cause | Fix | Status |
|---|---|---|---|---|---|
| 1 | Wines answered as plain text lists, not cards | team testing (earlier version) | Model chose `run_query` and typed a list | Rule in the prompt: any "show me wines" uses `recommend_wines` (cards) | Offline only |
| 2 | One answer showed a question, three wines, then three more (chosen wine plus two cheaper) | team, live site (risotto) | Model called several wine tools in one turn | Code rule: a turn shows a question OR one result set (blocked calls are refused); prompt rule | Offline only; real-model behaviour not re-tested |
| 3 | Chat asked customers for a photo or label | team, live site | Prompt did not say the chat is text only | "Text only" section: never ask for photos; says "planned for a future update" | Prompt text tested; model behaviour not re-tested |
| 4 | Food tag "game" unclear | team, live site | Tag name alone does not say wild game meat | Renamed "game meat"; prompt explains venison, wild boar, pheasant, hare | Offline |
| 5 | Prompt said "Dave from HEC Cave", the page said "cave." | team | Two naming decisions | Prompt changed to "cave." only | Offline |
| 6 | Contact email differed between prompt and page | us | Page edited by team, prompt not | Prompt takes the same address; test compares them | Offline |
| 7 | 12 tests failed after the 250-wine catalogue | us, test run | Tests had old counts, IDs and names hard-coded | Tests rewritten; one wine used for order tests | All offline tests pass |
| 8 | Invented tasting notes contradicted their aroma tags (e.g. oak, pepper, flint) | validator in the catalogue generator | Free-written notes vs fixed tags | Notes reworded until a check passes: every stated tag appears in the note | Checked by code |
| 9 | Invented names had repeated words, wrong French elision | us, review | Name lists combined blindly | Word lists and elision fixed | Checked by review of the CSV |
| 10 | Bottle label text could overflow with long names | us, render check | Fixed font size and width | Word wrap that also breaks at hyphens; producer line left out when it is already in the name, else cut at a word | Wrapping checked in code, not re-rendered |
| 11 | Attack input check flagged "I'm a manager at a restaurant" | us, own test | Pattern too broad | Pattern requires "the/your" or "of this shop" | Offline |
| 12 | My 700-token reply cap could cut off reasoning models mid-answer | us, code review (not seen in use) | Reasoning tokens count inside the cap | Default 2500, adjustable with `MAX_OUTPUT_TOKENS` | Not tested with a real model |
| 13 | A test asserted wine cards and chips together, which the new rule forbids | us, test run | Old rule | Test changed to match the rule | Offline |
| 14 | Runaway SQL query hung the test run when its limit was switched off | us, mutation check | No query limit | Step limit in the SQL tool | Verified: the test hangs without it |
| 15 | React front end and the real model could not be run in our build environment | us | No internet for npm and pip there | Front-end changes checked by syntax only; model replaced by a stand-in in tests | **Open risk**: first real run is on your machine |
| 16 | Pushing to GitHub from our build environment was refused | us | No write access | Files are uploaded by hand | Workaround |
| 17 | "Do you have a Japanese wine?" showed three unrelated wines and said "I can't access the catalog right now" (first real-model evaluation run, seed-08) | evaluation run | Country was only a ranking wish, so the best wines of other countries came back; our one-output rule then blocked the model's follow-up question and it reported the block as an outage. Exact tool arguments were not logged, so this is inferred from the call sequence | A country or region nobody has now returns no wines and a note; block messages say the catalogue works; prompt forbids outage claims; eval row checks the reply for outage wording | Fixed: passed in the second real run (1 run only, so not yet shown stable) |
| 18 | "Something sweet for dessert" showed nothing (seed-06) | evaluation run | "dessert" is not a food tag in the catalogue; the tool returned an error and the model gave up | "dessert", "venison" and similar words map to existing tags (fruit dessert, pastry, game meat) | Not fixed: second real run still showed no cards (the model asked a colour question instead). Tool arguments were not logged then; the evaluation now records them |
| 19 | "A 2020 Cabernet Sauvignon" was answered in text only, with a price and no card (seed-16) | evaluation run | recommend_wines had no vintage wish and the prompt sent vintage questions to run_query | New vintage wish (ranks, does not filter); prompt says wines must appear as cards, never recommended from run_query text | Fixed: second real run showed cards, named the one 2020 wine first and flagged the other vintages. Our test expected 2020 on every card, which the catalogue cannot satisfy, so the test was changed to a manual check |

## Not yet observed or measured
Two real-model runs exist so far (16 questions, one run each: 13 passed with $0.0585 total cost and median 17 s per answer, then 14 passed with $0.0512 and median 13.7 s); rows 17 to 19 come from them. Stability across repeated runs is not measured yet. Add rows from
`python eval_run.py --summarize ...` (failed runs) and from `redteam_run.py` (REVIEW lines), using the same columns.
Entries 1 to 6 describe fixes that came from the team's own testing; entries 7 to 16 come from our checks while building.
Earlier minor build problems (file layout mix-ups, cache folders in zip files, a helper function removed too early)
were fixed during development and are not listed because their details were not kept.
