# Sports Betting QA: Single Bet Placement

QA deliverables for the Single Bet Placement feature of the Sports Betting test application: a risk-based test plan, execution results with bug reports, a small Python automation framework with one UI and one API test, and a strategy note.

| Deliverable | Location |
|---|---|
| Test plan (6 prioritised scenarios) | [docs/TEST_PLAN.md](docs/TEST_PLAN.md) |
| Execution results and bug reports (18 defects, 3 Critical) | [docs/EXECUTION_REPORT.md](docs/EXECUTION_REPORT.md) |
| Strategy and recommendations | [docs/STRATEGY.md](docs/STRATEGY.md) |
| Automation framework | [src/betting_qa](src/betting_qa) |
| E2E UI test | [tests/ui/test_place_single_bet.py](tests/ui/test_place_single_bet.py) |
| API test | [tests/api/test_place_bet_balance_rule.py](tests/api/test_place_bet_balance_rule.py) |

**Headline finding:** the build is not releasable. The API accepts bets above the available balance and bets with a negative stake, a double click places two bets, and the receipt and on-screen balance disagree with the bet slip and the backend. Details are in the execution report.

## Stack

| Purpose | Tool |
|---|---|
| Language | Python 3.10+ |
| Test runner | Pytest |
| UI automation | Selenium WebDriver 4, desktop Chrome |
| API testing | `requests` |
| Configuration | `python-dotenv` (loads a local `.env`) |
| Lint and format (development only) | `ruff` |

Additional tooling was kept to a minimum. `python-dotenv` is there so the user id never has to be typed on the command line or committed. `ruff` enforces one code style. Chromedriver is resolved by Selenium Manager, which ships with Selenium, so there is no driver to install.

## Setup

Prerequisites: Python 3.10 or newer and a current desktop Chrome.

```bash
git clone <this-repository-url>
cd sports-betting-qa

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
# then edit .env and set QA_USER_ID=<your user id>
```

The user id is the only required setting. It is read from the environment, so `export QA_USER_ID=<your user id>` works as well as the `.env` file.

## Running the tests

```bash
pytest                  # both tests
pytest -m api           # API test only (no browser, a few seconds)
pytest -m ui            # UI test only (headless Chrome)
pytest -m ui --headed   # UI test with a visible browser window
```

Things to know before running:

- **Run serially.** Both tests use the same user account, and the application allows one bet in progress per user. Do not run with `pytest-xdist`.
- **The suite changes the account balance.** Every test resets the balance before and after it runs, so do not use the same user id for manual testing while the suite is running.
- When a UI test fails, a screenshot is saved to `artifacts/`.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `QA_USER_ID` | (required) | User id sent as `x-user-id` and as the `user-id` query parameter |
| `QA_BASE_URL` | `https://qae-assignment-tau.vercel.app` | Application under test |
| `QA_HEADLESS` | `1` | `0` shows the browser; `--headed` does the same for one run |
| `QA_UI_TIMEOUT` | `10` | Seconds to wait for UI elements |
| `QA_BET_TIMEOUT` | `20` | Seconds to wait for a bet to resolve to a receipt or an error |
| `QA_API_TIMEOUT` | `15` | Seconds before an API request times out |
| `QA_CHROME_BINARY`, `QA_CHROMEDRIVER` | unset | Explicit paths, only for machines where Chrome or the driver cannot be discovered automatically |

## What to expect on the current build

Both tests fail on Version 1.0.0. That is the intended outcome: each test asserts what the specification requires, and each one runs into defects that are documented in the execution report.

Last verified on 11 October 2026 with macOS, Python 3.13.7, Chrome 154, Selenium 4.51.0 and pytest 9.1.1: 2 failed in about 40 seconds, with exactly the checks listed below.

| Test | Failing check | Defect |
|---|---|---|
| `test_stake_above_available_balance_is_rejected` | A stake of 20.01 against a balance of 20.00 is answered with 200 instead of a validation error, and the balance becomes -0.01 | BUG-01 |
| `test_user_places_single_bet_and_receipt_matches_bet_slip` | Receipt lists the away team first | BUG-07 |
| | Receipt potential payout is stake x 2, not stake x odds | BUG-06 |
| | Header balance is unchanged after the bet although the backend balance dropped | BUG-05 |

The UI test uses soft assertions, so one run lists all three mismatches instead of stopping at the first. Everything else in the journey passes: bet slip content, the placement itself, receipt stake and odds, the cleared bet slip and the backend balance.

On a team these tests would be marked as expected failures linked to their tickets so the pipeline stays green until the fixes land (see the strategy note). They are left unmarked here so that a run shows plainly what they detect.

## Project structure

```
.
├── docs/
│   ├── TEST_PLAN.md               Part A: prioritised scenarios
│   ├── EXECUTION_REPORT.md        Part A: results and bug reports
│   ├── STRATEGY.md                Part C: strategy and recommendations
│   └── evidence/                  Screenshots referenced by the bug reports
├── src/betting_qa/                The framework (no test logic in here)
│   ├── config.py                  Settings read from the environment
│   ├── api/
│   │   ├── client.py              REST client, one method per endpoint
│   │   ├── models.py              Match and Selection domain objects
│   │   └── data_setup.py          Test-data helpers (pick a match, reach a balance)
│   ├── ui/
│   │   ├── driver_factory.py      Browser creation
│   │   ├── base.py                Explicit-wait helpers shared by all UI objects
│   │   ├── pages/betting_page.py  Page object for the application page
│   │   └── components/            Bet slip and bet receipt
│   └── utils/
│       ├── money.py               Decimal money parsing and payout calculation
│       └── soft_assert.py         Collect several failed checks into one failure
├── tests/
│   ├── conftest.py                Fixtures: settings, API client, browser, balance reset
│   ├── api/                       API tests
│   └── ui/                        UI tests
├── .github/workflows/tests.yml    Manually triggered CI run
├── pyproject.toml                 Pytest and ruff configuration
└── requirements.txt
```

## Design decisions

- **Tests state intent, the framework holds the mechanics.** Tests contain no locators, no waits and no URLs. A change to the page is fixed in one page object; a change to an endpoint is fixed in the client.
- **Page object plus components.** The application is one page with distinct parts, so the bet slip and the receipt are separate components owned by `BettingPage`. Locators use the application's element ids.
- **Explicit waits only.** No `sleep` and no implicit wait. Asynchronous values, such as the header balance, are polled until they match or time out, and the last value seen is reported.
- **The API is the source of truth.** Expected values (match, odds, balance) are read from the API at run time. Nothing is hard-coded, so the tests do not depend on a particular match existing or on a particular starting balance, and the UI is never compared with itself.
- **Money is `Decimal`.** All amounts are parsed and compared as decimals rounded to cents, because a one-cent difference is a real defect here and floats would hide or invent one.
- **Each test owns its state.** An autouse fixture resets the balance before and after every test, so tests can run in any order.
- **Negative tests get raw responses.** `place_bet` returns the `requests.Response` so a test can assert on status, error code and body; read helpers return domain values.

## Extending the suite

- **New API test:** add a file under `tests/api/`, mark it with `pytest.mark.api`, and use the `api_client` and `upcoming_match` fixtures. The stake-limit matrix from TC-03 is a natural `pytest.mark.parametrize` candidate.
- **New UI test:** add a file under `tests/ui/`, mark it with `pytest.mark.ui`, and use the `betting_page` fixture. Add locators and actions to the page object or a component, never to the test.
- **Another environment:** set `QA_BASE_URL`.

Lint before committing: `pip install -r requirements-dev.txt && ruff check . && ruff format --check .`
