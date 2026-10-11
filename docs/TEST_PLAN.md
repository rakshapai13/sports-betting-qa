# Test Plan: Single Bet Placement

| | |
|---|---|
| Feature | Single Bet Placement (desktop web, football, pre-match, single bets) |
| Basis | Feature Specification "Single Bet Placement", Swagger at `/api/docs` |
| Application | https://qae-assignment-tau.vercel.app (Version 1.0.0) |
| Layers under test | UI (bet slip, receipt, modals, filters) and REST API |

## How I chose the scenarios

The feature takes money from a balance, so I ranked everything by one question: if this breaks, does somebody lose money, or see a wrong amount on screen?

- Balance and bet integrity come first: wrong balance, a bet the user cannot afford, a bet placed twice.
- The spec marks most rules as "UI + API". I test the money rules on both, because the UI check can be skipped by calling the API directly.
- The same bet is shown three times (bet slip, API response, receipt). They have to agree.
- With only six scenarios I put each one on a boundary: min and max stake, exact balance, edges of a filter range.

The scenarios are in priority order. I executed the first three; results are in [EXECUTION_REPORT.md](EXECUTION_REPORT.md).

| ID | Title | Priority | Type |
|---|---|---|---|
| TC-01 | Place a single bet end to end; bet slip, receipt and balance agree | Critical | Happy path |
| TC-02 | A stake cannot exceed the available balance (UI + API) | Critical | Negative / boundary |
| TC-03 | Stake limits and input validation (UI + API) | High | Boundary / negative |
| TC-04 | One submission creates exactly one bet (double click, concurrency, failure and Rebet) | High | Negative / resilience |
| TC-05 | Only upcoming matches can be bet on; invalid match and selection are rejected | High | Business rule / negative |
| TC-06 | Date and odds filters apply inclusive ranges and reject invalid ranges | Medium | Functional / boundary |

Precondition for all scenarios: reset the balance with `POST /api/reset-balance`, read the starting balance with `GET /api/balance`, and open the app at `/?user-id=<user-id>` in desktop Chrome.

---

## TC-01: Place a single bet end to end; bet slip, receipt and balance agree

**Priority:** Critical

**Risk rationale:** This is the main journey and the only way the product earns money, so it has to work on every build. It is also the only scenario where the match data, the bet slip calculation, the API, the receipt and the balance are checked together. The risk I care about most is that they disagree: the customer accepts one payout on the bet slip and gets a different one on the receipt, or the balance on screen does not go down. Both end in a complaint, and a wrong balance lets the customer bet money they no longer have.

**Test data:** an upcoming match, e.g. Monaco vs Lyon, outcome `1` (home) at 2.15; stake €10.00.

**Steps**

1. Note the starting balance `B` from `GET /api/balance`. Open the application.
2. Check the balance in the header and in the empty bet slip.
3. Click the `1` odds button of the match.
4. Enter `10` in the stake field.
5. Review the bet slip.
6. Click **Place Bet** and watch the button.
7. Review the receipt modal.
8. Click **Close** on the receipt.
9. Check the bet slip, the header balance and `GET /api/balance`.

**Expected result**

- Step 2: both balances show `B`.
- Step 3: the button is highlighted; the bet slip shows one selection.
- Step 5: bet slip shows "Monaco vs Lyon", outcome Home, odds 2.15, total stake €10.00, potential payout €21.50 (stake x odds), and the available balance. Place Bet is enabled.
- Step 6: button shows "Placing..." and the flow resolves to exactly one outcome.
- Step 7: receipt shows a Bet ID, match "Monaco vs Lyon" (home team first), selection Home, stake €10.00, odds 2.15, potential payout €21.50 and a placement timestamp. All values equal those on the bet slip and in the `POST /api/place-bet` response (currency EUR).
- Step 8/9: the modal closes, no selection is active, and the header, the bet slip and the API all show `B - 10.00`.

---

## TC-02: A stake cannot exceed the available balance (UI + API)

**Priority:** Critical

**Risk rationale:** This rule stops a customer from betting money they do not have. If it fails, the balance goes negative, which is a direct loss for the operator and in a regulated market also a compliance problem. The UI check is not enough on its own, because it can be bypassed and it depends on the balance in the browser being up to date. So I test the boundary (one cent over, exactly equal) on both layers, and I repeat the UI check after a bet has changed the balance.

**Test data:** balance brought to €20.00 (below the €100 stake cap, so the balance rule is the only rule in play).

**Steps**

1. Reset the balance, then place valid bets through the API until `GET /api/balance` returns 20.00.
2. API: `POST /api/place-bet` with a valid match and selection and `stake: 20.01`. Then `GET /api/balance`.
3. Bring the balance back to 20.00 if step 2 changed it. Reload the application.
4. UI: select any odds and enter `20.01`.
5. UI: change the stake to `20.00` and place the bet. Close the receipt.
6. UI, without reloading: select odds again, enter `20.00` and try to place the bet.
7. `GET /api/balance`.

**Expected result**

- Step 2: the request is rejected with a 4xx validation error identifying insufficient balance; the balance is still 20.00.
- Step 4: message "Insufficient balance"; Place Bet is disabled.
- Step 5: the bet is accepted (a stake equal to the balance is allowed); balance is €0.00 in the header, in the bet slip and in the API.
- Step 6: message "Insufficient balance"; Place Bet is disabled; no request is sent.
- Step 7: balance is 0.00. At no point is the balance negative.

---

## TC-03: Stake limits and input validation (UI + API)

**Priority:** High

**Risk rationale:** The stake limits (€1.00 to €100.00, two decimals) cap how much the operator can lose on one bet, and limits are where off-by-one mistakes usually sit. Invalid stakes worry me more than out-of-range ones: a negative or non-numeric value that reaches the balance calculation could change the balance in the wrong direction. The UI blocks most of these at the keyboard, so the API has to be tested directly with values the UI would never send.

**Test data:** balance at the reset value; any upcoming match; selection HOME.

**Steps**

For each stake below, (a) enter it in the bet slip and observe the field, message and Place Bet button; (b) send it with `POST /api/place-bet` and then read `GET /api/balance`.

| # | Stake | Expected in UI | Expected from API |
|---|---|---|---|
| 1 | empty / field missing | Place Bet disabled | 422, stake invalid |
| 2 | `abc` (API: `"abc"`, `"10"`, `null`, `true`) | characters not accepted | 422, stake must be a number |
| 3 | `-5` | minus sign not accepted | 422, below minimum |
| 4 | `0` | "Minimum stake is €1.00", disabled | 422, below minimum |
| 5 | `0.99` | "Minimum stake is €1.00", disabled | 422, below minimum |
| 6 | `1.00` | accepted, enabled | 200 (see note) |
| 7 | `1.01` | accepted, enabled | 200 |
| 8 | `100.00` | accepted, enabled | 200 |
| 9 | `100.01` | "Maximum stake is €100.00", disabled | 422, above maximum |
| 10 | `10.123` | third decimal not accepted | 422, invalid precision |

**Expected result**

- Every rejected value produces the stated message or error, and the balance is unchanged after each rejected API call.
- Every accepted value reduces the balance by exactly the stake, and the payout equals stake x odds.
- No input results in a balance increase.

**Note on the minimum:** the spec is not consistent. Section 3 and the UI text in 4.4 say the minimum is €1.00, the table in 4.1 says "Minimum €1.01". I treat €1.00 as valid and list it as an open question.

---

## TC-04: One submission creates exactly one bet

**Priority:** High

**Risk rationale:** Placing a bet takes a couple of seconds, and that is when people click again. A second request means a second stake taken for a bet the customer did not want. The failure path has the same risk: Rebet must retry once, and a failed attempt must not take any money. The spec describes the guards (loading state, one final outcome, `409` when a bet is already in progress), so I check each of them.

**Steps**

1. Select odds, enter stake `2`, and double-click **Place Bet** quickly. Count the `POST /api/place-bet` requests in the browser's network tab and compare the balance before and after.
2. API: send two identical `POST /api/place-bet` requests at the same moment. Compare the responses and the balance.
3. Force a failed placement (for example block or stub the `place-bet` request to return 500). Observe the modal and the balance.
4. In the error modal click **Rebet** (with the stub removed).
5. Repeat step 3, then click **Close**. Repeat again and use the top-right **X**.

**Expected result**

- Step 1: the button shows "Placing..." and accepts no further clicks; exactly one request is sent, one receipt is shown and the balance drops by 2.00 once.
- Step 2: one request succeeds, the other is rejected with `409`; the balance drops by one stake.
- Step 3: modal titled "Something went wrong" explaining that the bet could not be processed and suggesting to try again, with **Rebet** (primary) and **Close** (secondary). The balance is unchanged.
- Step 4: the modal closes, placement is retried once and the receipt appears; the balance drops by one stake.
- Step 5: Close and X both close the modal and clear the selection and stake; the balance is unchanged.

---

## TC-05: Only upcoming matches can be bet on; invalid match and selection are rejected

**Priority:** High

**Risk rationale:** The feature is pre-match only. A bet on a match that has already started or finished is a bet on a known result, which is an easy way for a sportsbook to lose money. The API has to enforce this itself, and also validate the match id and the selection, because the UI can be bypassed.

**Steps**

1. Open the application and compare each listed match's kickoff date with today's date.
2. If any past match is listed, try to select its odds and place a €1.00 bet in the UI.
3. API: `POST /api/place-bet` with the id of a match whose `kickoffDate` is in the past.
4. API: send requests with `matchId` missing, empty, blank, and unknown.
5. API: send requests with `selection` missing, `"home"`, `"WIN"`, and `null`.
6. API: send a valid bet for each of HOME, DRAW and AWAY on a match with three different prices.
7. In the UI, click `1` on one match, then `X` on the same match, then `2` on another match.

**Expected result**

- Step 1: only matches with a kickoff after the current date and time are listed.
- Steps 2-3: a past match cannot be selected in the UI, and the API rejects the bet with a 422 without changing the balance.
- Steps 4-5: each request is rejected with 422 and the documented error code (`invalid_match_id`, `invalid_match`, `invalid_selection`); the balance is unchanged.
- Step 6: each response returns the price of the requested outcome and payout = stake x that price.
- Step 7: each click replaces the previous selection; the bet slip always holds exactly one selection.

---

## TC-06: Date and odds filters apply inclusive ranges and reject invalid ranges

**Priority:** Medium

**Risk rationale:** Filters do not touch money, so a bug here is a usability problem and not a financial one. That is why this is last. It still matters, because a filter that drops matches at the edge of a range hides events the customer could bet on, and the spec is clear that ranges are inclusive and invalid ranges must be rejected with a message.

**Steps**

1. Date filter: select a single day that has a match and apply.
2. Date filter: select a range whose first and last day both have a match and apply.
3. Date filter: open, pick another date, click **Cancel**. Then use **Reset**.
4. Odds filter: set min and max to the same value that exists in the list (for example 1.35 to 1.35) and apply.
5. Odds filter: apply 2.00 to 3.00 and compare the result with the data from `GET /api/matches`.
6. Odds filter: enter min 3.00 and max 2.00 and apply.
7. With a filter active, read the "Showing N matches" counter and place a bet on a filtered match.

**Expected result**

- Step 1: only matches on that day are listed.
- Step 2: matches on the first day, the last day and every day between are listed.
- Step 3: Cancel leaves the applied filter and its label unchanged; Reset returns to all matches.
- Step 4: matches priced exactly at the boundary value are listed.
- Step 5: every match with a price inside 2.00 to 3.00, boundaries included, is listed and no others.
- Step 6: the range is rejected with a clear message and the list is not changed.
- Step 7: the counter equals the number of matches displayed; betting works as in TC-01.

---

## Not covered

Live betting, accumulators, other sports and mobile layouts are out of scope in the spec. Bet settlement, load, accessibility and other browsers are not covered by these six scenarios.
