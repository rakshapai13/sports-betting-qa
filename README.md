# Sports Betting QA - Single Bet Placement

My submission for the QA take-home on the Single Bet Placement feature.

| Part | What | Where |
|---|---|---|
| A | Test plan, 6 prioritised scenarios | [docs/TEST_PLAN.md](docs/TEST_PLAN.md) |
| A | Execution results and bug reports | [docs/EXECUTION_REPORT.md](docs/EXECUTION_REPORT.md) |
| B | Automation framework | [src/betting_qa](src/betting_qa) |
| B | E2E UI test | [tests/ui/test_place_single_bet.py](tests/ui/test_place_single_bet.py) |
| B | API test | [tests/api/test_place_bet_balance_rule.py](tests/api/test_place_bet_balance_rule.py) |
| C | Strategy and recommendations | [docs/STRATEGY.md](docs/STRATEGY.md) |

In short: I found 18 defects, 3 of them Critical. The API accepts bets above the balance and bets with a negative stake, and a double click on Place Bet places the bet twice. The receipt and the on-screen balance also disagree with the bet slip and the backend. Details are in the execution report.

## Stack

- Python 3.10+
- Pytest
- Selenium WebDriver 4 with desktop Chrome
- `requests` for the API

Two extras: `python-dotenv`, so the user id can live in a local `.env` file instead of the command line, and `ruff` for linting (dev only). There is no driver to install, Selenium Manager downloads the right chromedriver on the first run.

## Setup

You need Python 3.10 or newer and Google Chrome.

```bash
git clone https://github.com/rakshapai13/sports-betting-qa.git
cd sports-betting-qa
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

`.env.example` already contains my user id, so the copied `.env` works as it is. To run as a different user, change `QA_USER_ID` in `.env` (or export it as an environment variable).

## Running

```bash
pytest                  # both tests
pytest -m api           # API test only
pytest -m ui            # UI test only, headless
pytest -m ui --headed   # UI test with the browser visible
```

A few things to know:

- Run the tests one at a time, not in parallel. They share one user account and the app allows only one bet in progress per user.
- The tests reset the balance of that user before and after each test, so don't test manually with the same id while they run.
- If the UI test fails, a screenshot is saved in `artifacts/`.

Settings, read from `.env` or the environment:

| Variable | Default | |
|---|---|---|
| `QA_USER_ID` | `candidate-5LxhoJ9UlGpX` (from `.env`) | user the tests run as |
| `QA_BASE_URL` | `https://qae-assignment-tau.vercel.app` | app under test |
| `QA_HEADLESS` | `1` | set to `0` to see the browser |

## Current result

Both tests fail against Version 1.0.0, and they should: each one hits a real defect from the bug report.

| Test | What fails | Bug |
|---|---|---|
| `test_stake_above_available_balance_is_rejected` | Stake 20.01 with balance 20.00 returns 200 and the balance becomes -0.01 | BUG-01 |
| `test_user_places_single_bet_and_receipt_matches_bet_slip` | Receipt shows the away team first | BUG-07 |
| | Receipt payout is stake x 2 instead of stake x odds | BUG-06 |
| | Header balance does not change after the bet | BUG-05 |

The rest of the UI journey passes (bet slip values, placing the bet, receipt stake and odds, slip cleared, API balance reduced). The UI test uses soft assertions, so the three mismatches come out in one run.

Last run: 11 October 2026 on macOS, Python 3.13, Chrome 154.

I left the tests failing on purpose so the run shows what they catch. In a real pipeline I would mark them as expected failures linked to the bug tickets until the fixes are in.

## Structure

```
docs/                     test plan, execution report, strategy, screenshots
src/betting_qa/
    config.py             settings from the environment
    api/client.py         one method per endpoint
    api/models.py         Match and Selection
    api/data_setup.py     pick a match, bring the balance to a known value
    ui/base.py            explicit-wait helpers
    ui/driver_factory.py  starts Chrome
    ui/pages/             page object for the betting page
    ui/components/        bet slip and receipt
    utils/money.py        Decimal money helpers
    utils/soft_assert.py  collect several failed checks into one failure
tests/
    conftest.py           fixtures
    api/                  API tests
    ui/                   UI tests
```

## Notes on the framework

- The test files have no locators or waits on purpose (Page Object Model). A test only calls methods like `select_odds()`, `enter_stake()` or `place_bet()`. The locators are in `src/betting_qa/ui/pages/betting_page.py` and `src/betting_qa/ui/components/` (bet slip and receipt), and the HTTP calls are in `src/betting_qa/api/client.py`. When the UI changes, only those files need updating, not the tests.
- No `sleep` and no implicit waits, only explicit waits.
- Expected values (match, odds, balance) are read from the API at run time. Nothing is hard-coded, so the tests keep working when the match list changes.
- Amounts are compared as `Decimal`. With floats a one-cent difference can get lost, and one cent is a real bug here.
- Every test resets the balance first, so the order of the tests does not matter.

To add a test, put it under `tests/api` or `tests/ui`, mark it with `api` or `ui`, and use the existing fixtures (`api_client`, `upcoming_match`, `betting_page`).
