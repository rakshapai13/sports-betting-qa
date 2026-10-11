# Test Plan: Single Bet Placement

| | |
|---|---|
| Feature | Single Bet Placement (desktop web, football, pre-match, single bets) |
| Basis | Feature Specification "Single Bet Placement", Swagger at `/api/docs` |
| Application | https://qae-assignment-tau.vercel.app (Version 1.0.0) |
| Layers under test | UI (bet slip, receipt, modals, filters) and REST API |

## How the scenarios were chosen

The feature moves money, so the scenarios are ranked by one question: **if this breaks, does the customer or the operator lose money or lose trust in a number on the screen?**

1. **Money integrity first.** Anything that can produce a wrong balance, an unfunded bet or a duplicate bet outranks everything else.
2. **The API is the last line of defence.** The spec assigns most validation rules to "UI + API". UI checks are a convenience and can be bypassed, so every money rule is tested on both layers.
3. **Consistency across the journey.** The same bet is shown three times (bet slip, API response, receipt). Disagreement between them is a customer dispute even when the backend is correct.
4. **Boundaries over volume.** Six scenarios cannot cover every input, so each one sits on a boundary (min/max stake, exact balance, range edges) where defects cluster.

Six scenarios are listed in priority order. The first three were executed formally; results and defects are in [EXECUTION_REPORT.md](EXECUTION_REPORT.md).

| ID | Title | Priority | Type |
|---|---|---|---|
| TC-01 | Place a single bet end to end; bet slip, receipt and balance agree | Critical | Happy path |
| TC-02 | A stake cannot exceed the available balance (UI + API) | Critical | Negative / boundary |
| TC-03 | Stake limits and input validation (UI + API) | High | Boundary / negative |
| TC-04 | One submission creates exactly one bet (double click, concurrency, failure and Rebet) | High | Negative / resilience |
| TC-05 | Only upcoming matches can be bet on; invalid match and selection are rejected | High | Business rule / negative |
| TC-06 | Date and odds filters apply inclusive ranges and reject invalid ranges | Medium | Functional / boundary |

Common precondition for all scenarios: a valid user id; balance reset with `POST /api/reset-balance` and the starting balance read back with `GET /api/balance`; application opened at `/?user-id=<user-id>` in desktop Chrome.

---

## TC-01: Place a single bet end to end; bet slip, receipt and balance agree

**Priority:** Critical

**Risk rationale:** This is the product's only revenue path and the journey every customer takes. It is also the only place where match data, bet slip maths, the placement API, the receipt and the balance are exercised together. The specific risk is inconsistency: the customer agrees to one payout on the bet slip and is confirmed a different one, or the balance on screen does not reflect the bet. Either becomes a dispute, and a wrong balance can lead the customer to bet money they no longer have.

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

**Risk rationale:** This rule stops customers from betting money they do not have. If it fails the account goes negative, which is a direct financial loss for the operator and a regulatory problem (betting on credit). The UI check alone is not a control, because it can be bypassed and it depends on the balance shown in the browser being current. The scenario therefore tests the boundary (one cent over, exactly equal) on both layers, and re-checks the UI after a bet has changed the balance.

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

**Risk rationale:** Stake limits (€1.00 to €100.00, two decimals) are the operator's exposure limits, and off-by-one errors at limits are the most common validation defect. Malformed stakes are the more dangerous half: a negative or non-numeric stake that reaches the balance calculation can corrupt the balance outright. The UI restricts what can be typed, so the API has to be tested directly with values the UI would never send.

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

**Note on the minimum:** the spec contradicts itself. Section 3 and the UI copy in 4.4 say the minimum is €1.00; the table in 4.1 says "Minimum €1.01". This plan treats €1.00 as valid and raises the contradiction as a spec question.

---

## TC-04: One submission creates exactly one bet

**Priority:** High

**Risk rationale:** Placement takes a couple of seconds, which is exactly when an impatient customer clicks again. A second request means a second stake taken for a bet the customer did not intend, with only one receipt to show for it. The same applies to the failure path: "Rebet" must retry once, and a failed attempt must not take money. The spec defines the guards (loading state, one final outcome, `409` for a bet already in progress), so each is checked.

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

**Risk rationale:** The feature is pre-match only. A bet accepted on a match that has already kicked off or finished is a bet on a known result, which is the classic way a sportsbook loses money to abuse. The API must enforce this itself, along with the identity of the match and outcome, because the UI can be bypassed.

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

**Risk rationale:** Filters do not move money, so a defect here costs usability rather than funds; that is why this scenario ranks last. It still matters: a filter that silently drops matches at the edge of a range hides bettable events from customers, and the spec is explicit that ranges are inclusive and that invalid ranges must be rejected with clear feedback.

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

## Out of scope for this plan

Live betting, accumulators, other sports and mobile layouts are excluded by the specification. Bet settlement, performance under load, accessibility and cross-browser behaviour are not covered by these six scenarios; they are discussed in [STRATEGY.md](STRATEGY.md).
