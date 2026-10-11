# Strategy and Recommendations

## 1. Why these two tests were automated

With a budget of two tests, each one has to earn its place. Candidates were scored on four questions:

- **Risk:** what does it cost if this breaks in production?
- **Frequency:** how often does a customer hit it, and how often would a tester have to repeat it?
- **Stability:** can it be automated deterministically against this environment?
- **Layer:** is this the cheapest layer at which the check is still meaningful?

| Candidate | Risk | Frequency | Stable to automate | Decision |
|---|---|---|---|---|
| Place a single bet end to end (UI) | Highest: the revenue path | Every customer, every release | Yes | **Automated (UI)** |
| Stake cannot exceed balance (API) | Highest: unfunded bets | Every release | Yes | **Automated (API)** |
| Stake min / max / precision matrix (API) | High | Every release | Yes | Next to automate |
| Duplicate submission on double click | High | Occasional | Timing-dependent in the UI | Manual for now |
| Failure path: error modal, Rebet | High | Rare | No failure trigger available | Manual for now |
| Past matches not bettable | High | Every release | Needs date control | Next to automate (API) |
| Date and odds filters | Medium | Occasional | Yes, but costly in the UI | Manual |

**E2E UI test: `test_user_places_single_bet_and_receipt_matches_bet_slip`.** It covers the one journey the feature exists for, and it is the only test that sees the parts working together: match list, bet slip, placement request, receipt and balance. Its assertions are about consistency (what the customer agreed to on the bet slip equals what the receipt confirms equals what the backend stored), which is where the most damaging defects in this build were found: wrong receipt payout, reversed teams and a stale balance. A single run reports all of them because the checks are soft. Expected values come from the API rather than from the screen, so the UI is never compared with itself.

**API test: `test_stake_above_available_balance_is_rejected`.** Of all the validation rules this is the one that protects real money, and it must hold on the server because the UI check can be bypassed and relies on a balance that may be out of date. The test is a boundary test: it first brings the balance below the stake cap so that the balance rule is the only rule in play, then stakes one cent more than the balance and asserts on the response and on the stored balance. It needs no browser, runs in a few seconds and is deterministic, so it can gate every commit.

Together the two tests cover both layers, one happy path and one negative boundary, and the two outcomes the business can least afford: a customer who cannot place a correct bet, and a customer who can place a bet they cannot pay for.

## 2. What was left manual, and why

| Area | Why it stays manual for now |
|---|---|
| **Exploratory testing around placement** | Rapid clicks, odd inputs, switching selections mid-flow. This is where unknown defects are found; most of the bug report came from here, not from scripted steps. Automation only re-checks what someone has already thought of. |
| **Duplicate submission (double click)** | High risk, but in the UI it depends on click timing, which makes an automated version flaky. The durable fix is an idempotency key on the API; once that exists it becomes a simple, stable API test. Until then a short manual check per release is more reliable. |
| **Failure path (error modal, Rebet, Close)** | The application offers no way to make a placement fail on demand. Testing it needed a stubbed response in the browser. Worth automating as a component test with a mocked API (see 3.1), not as a black-box E2E test. |
| **Filters (calendar and odds range)** | Medium risk and expensive to automate through a date picker and sliders; the UI would change faster than the test pays back. The filtering logic itself belongs in unit tests. |
| **Receipt and modal content, copy, layout** | Judging whether a receipt is clear and complete to a customer is a human call. A missing field such as the selection was noticed by reading the receipt against the spec, not by a locator. |
| **Spec contradictions** | Minimum stake 1.00 or 1.01, initial balance 125.50 or 120.00, payout rounding. These need a product decision before any check can be written down as pass or fail. |

## 3. Recommendations if this project were to scale

### 3.1 Move checks down the pyramid and keep the UI layer thin

Most rules in the spec are "UI + API" validation rules, and the Critical defects found were all on the API. Put the volume there:

- **API tests** for the whole validation table as one parametrised matrix (stake limits, precision, types, selection, match id, auth, methods), each case asserting status, error code and unchanged balance. Add **contract tests** generated from the published OpenAPI document so that deviations such as `currency: "USD"`, the 500 on malformed JSON or the 200 on `GET /api/place-bet` are caught without hand-written cases.
- **Component tests** for the bet slip and the modals against a mocked API. This is the right home for the loading state, double-click protection, the error modal and Rebet, and balance refresh: fast, deterministic and able to force failures.
- **UI end-to-end tests** limited to three to five journeys (place a bet, rejected stake, failed placement and retry). They prove the wiring; they should not carry the rule coverage.

### 3.2 Build a pipeline that gives feedback in minutes and makes known defects visible

- **On every pull request:** lint and API tests (under a minute). **On merge:** UI smoke tests against a preview deployment of that commit. **Nightly:** the full suite. A manual workflow is included in `.github/workflows/tests.yml` as a starting point.
- Publish JUnit results and failure screenshots as build artifacts (the framework already saves a screenshot on UI failure).
- Tests that fail because of a known, ticketed defect should be marked as expected failures linked to the ticket, in strict mode, so the build stays green for new work, the defect stays visible, and the test fails loudly the day the fix lands and the marker has to be removed. New failures in Critical tests block the release.

### 3.3 Make test data and the environment controllable

The current environment limits how far automation can go, and each limit has a concrete fix:

- **One shared, stateful account.** Tests must run serially and can be disturbed by anyone using the same user. Provide a way to create a throwaway user per test (or a pool of users per CI worker). That unlocks parallel runs.
- **No way to set a balance.** The API test spends real bets to reach 20.00. A test-only "set balance" endpoint, and a reset that actually returns the documented 125.50, would make set-up one call.
- **A catalogue tied to real dates.** 83 of 103 matches are already in the past and the rest will follow, so any test that needs an upcoming match will eventually stop finding one. Seed matches relative to the current date, or allow the clock to be injected in test environments.
- **No failure injection.** A test-only switch (for example a request header that forces a 500, a timeout or a slow response) would let the failure and retry paths be tested end to end.
- **Idempotency.** An idempotency key on `POST /api/place-bet` fixes the duplicate-bet defect at its root and makes retries safe to test.

### 3.4 Spec clarifications to request

Small, but each one currently blocks a clear pass/fail verdict:

1. Minimum stake: €1.00 (section 3, UI copy) or €1.01 (table 4.1)?
2. Initial balance: 125.50 (domain notes, reset response) or 120.00 (stored value)?
3. Payout rounding: half-up to the cent, or truncation? Stated once, applied by UI and API alike.
4. Is a stake exactly equal to the balance allowed? (Assumed yes.)
5. Definition of "upcoming": kickoff date after today, or kickoff time after now, and in which time zone?
6. Who issues the Bet ID? The API response has none.
7. Odds filter: does a match qualify if any outcome is in range, or only if all are?
8. Which HTTP status and error code does the API use for insufficient balance? The Swagger schema shows `insufficient_balance` only as an example.
