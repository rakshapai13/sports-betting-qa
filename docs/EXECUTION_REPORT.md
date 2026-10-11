# Execution Results and Bug Reports

| | |
|---|---|
| Build | Version 1.0.0 at https://qae-assignment-tau.vercel.app |
| Executed | 11 October 2026 |
| Environment | Desktop Chromium-based browser for the UI; API requests sent with the `x-user-id` header |
| Scope | TC-01, TC-02, TC-03 from [TEST_PLAN.md](TEST_PLAN.md), plus exploratory checks around bet placement |
| Test data | Balance reset with `POST /api/reset-balance` before each scenario; balances quoted below are read from `GET /api/balance` |

## Summary

**The build is not releasable.** All three executed scenarios failed, and the failures are in the money path:

- The API accepts bets the user cannot afford and bets with a negative stake, so a balance can go below zero or be increased at will (BUG-01, BUG-02).
- Clicking Place Bet twice places and charges two bets (BUG-03).
- The balance on screen is never updated after a bet, and the receipt confirms a different payout and the wrong team order from what the user agreed to on the bet slip (BUG-05, BUG-06, BUG-07).
- Matches that have already been played are listed and can be bet on (BUG-04).

| Scenario | Result | Defects raised |
|---|---|---|
| TC-01 Place a single bet end to end | **Failed** | BUG-05, BUG-06, BUG-07, BUG-08, BUG-09, BUG-11, BUG-18 |
| TC-02 Stake cannot exceed balance | **Failed** | BUG-01 (with BUG-05 as the UI route to it) |
| TC-03 Stake limits and validation | **Failed** | BUG-02, BUG-10 |
| Exploratory checks | 8 further defects | BUG-03, BUG-04, BUG-12 to BUG-17 |

| Severity | Count | Bugs |
|---|---|---|
| Critical | 3 | BUG-01, BUG-02, BUG-03 |
| High | 5 | BUG-04, BUG-05, BUG-06, BUG-07, BUG-08 |
| Medium | 7 | BUG-09 to BUG-15 |
| Low | 3 | BUG-16, BUG-17, BUG-18 |

Severity scale: **Critical** = direct financial loss or corrupted balance; **High** = customer is shown wrong money or bet information, or a core business rule is not enforced; **Medium** = contract or spec deviation with a workaround or limited reach; **Low** = cosmetic or minor usability.

---

## Scenario results

### TC-01: Place a single bet end to end (Failed)

Data: Monaco vs Lyon, outcome `1` at 2.15, stake €10.00. Starting balance 120.00.

| Step | Result | Observation |
|---|---|---|
| 1-2 Balance after reset | Fail | Header and bet slip show €120.00 and match the API, but the reset response and the domain notes say 125.50 (BUG-08) |
| 3 Select odds | Pass | Button highlighted, one selection in the bet slip |
| 4-5 Bet slip content | Pass with remark | Monaco vs Lyon, Match Winner: Home, odds 2.15, total stake €10.00, potential payout €21.50. The available balance is no longer shown once a selection is active (BUG-18) |
| 6 Place Bet | Pass | Button shows "Placing...", receipt appears after about 2.5 s. `POST /api/place-bet` returns 200 with payout 21.5, balance 110, but `currency: "USD"` (BUG-09) |
| 7 Receipt | Fail | Match shown as "Lyon vs Monaco" (BUG-07); potential payout €20.00 instead of €21.50 (BUG-06); no selection shown (BUG-11). Bet ID, stake €10.00, odds 2.15 and a timestamp are present |
| 8 Close receipt | Pass | Modal closes, selection cleared |
| 9 Balance after bet | Fail | API balance 110.00; header and bet slip still show €120.00 (BUG-05) |

### TC-02: A stake cannot exceed the available balance (Failed)

| Step | Result | Observation |
|---|---|---|
| 1 Balance at 20.00 | Pass | Reset, then one €100.00 bet |
| 2 API stake 20.01 | Fail | 200 "Bet placed successfully", balance -0.01 (BUG-01) |
| 4 UI stake 20.01 (fresh page, balance 20.00) | Pass | "Insufficient balance", Place Bet disabled |
| 5 UI stake 20.00 | Fail | Bet accepted and API balance is 0.00 as expected, but header and bet slip still show €20.00 (BUG-05) |
| 6 UI stake 20.00 again, no reload | Fail | No warning, Place Bet enabled, bet accepted |
| 7 Final balance | Fail | API balance -20.00 while the UI shows €20.00 (BUG-01 reached through the UI alone) |

### TC-03: Stake limits and input validation (Failed)

| # | Stake | UI | API |
|---|---|---|---|
| 1 | empty / missing | Pass: Place Bet disabled | Pass: 422 `invalid_stake_type` |
| 2 | `abc`, `"10"`, `null`, `true` | Pass: letters cannot be typed | Pass: 422 `invalid_stake_type` |
| 3 | `-5` | Pass: minus sign is dropped | **Fail: 200, balance increased by 5.00 (BUG-02)** |
| 4 | `0` | Pass: "Minimum stake is €1.00" | Pass: 422 `invalid_stake_min` |
| 5 | `0.99` | Pass: "Minimum stake is €1.00" | Pass: 422 `invalid_stake_min` |
| 6 | `1.00` | Pass: accepted | Pass: 200, balance -1.00 |
| 7 | `1.01` | Pass: accepted | Pass: 200, balance -1.01 |
| 8 | `100.00` | Pass: accepted | Pass: 200, balance -100.00 |
| 9 | `100.01` | Pass: "Maximum stake is €100.00" | Pass: 422 `invalid_stake_max` |
| 10 | `10.123` | Pass: third decimal cannot be typed | Pass: 422 `invalid_stake_precision` |

The balance was unchanged after every rejected request. Payout was correct for the values above except where stake x odds does not land exactly on a cent; see BUG-10.

---

## Bug reports

### BUG-01: API accepts a stake higher than the available balance, leaving a negative balance

**Severity:** Critical

**Reproduction steps**

1. `POST /api/reset-balance`, then `POST /api/place-bet` with `{"matchId":"ligue-1-monaco-lyon-2026-10-14","selection":"HOME","stake":100}`.
2. `GET /api/balance` returns `{"balance":20,"currency":"EUR"}`.
3. `POST /api/place-bet` with the same match and selection and `"stake": 20.01`.
4. `GET /api/balance`.

**Expected:** Step 3 is rejected as insufficient balance (spec 4.1: "Must not exceed available balance", UI + API; the Swagger error example is `insufficient_balance`). Balance stays 20.00.

**Actual:** Step 3 returns `200 {"message":"Bet placed successfully", "stake":20.01, "payout":43.02, "balance":-0.01, ...}`. Step 4 returns `-0.01`. Also reproduced with stake 96.57 against a balance of 96.56. There is no lower limit: with the UI route described in BUG-05 the account reached -95.00 and -20.00 in two separate runs.

**Business impact:** Customers can bet money they do not have. The operator carries the loss on every unfunded losing bet and pays out on unfunded winning ones, and betting on credit is a compliance breach in regulated markets.

**Evidence:** Response bodies quoted above. [05-stale-ui-balance-vs-api.jpg](evidence/05-stale-ui-balance-vs-api.jpg) shows the API reporting -20.00.

---

### BUG-02: API accepts a negative stake and credits the balance

**Severity:** Critical

**Reproduction steps**

1. `GET /api/balance` (120.00 after a reset).
2. `POST /api/place-bet` with `{"matchId":"ligue-1-monaco-lyon-2026-10-14","selection":"HOME","stake":-5}`.
3. `GET /api/balance`.

**Expected:** 422 `invalid_stake_min` ("Stake must be at least 1.00."), as returned for 0 and 0.99. Balance unchanged.

**Actual:** `200 {"message":"Bet placed successfully","stake":-5,"odds":2.15,"payout":-10.75,"balance":125,"currency":"USD"}`. The balance went from 120.00 to 125.00. The minimum check works for 0 to 0.99 but not below zero.

**Business impact:** Anyone who calls the API directly can add funds to their own account in any amount (repeat with -100). This is free money on demand. The UI strips the minus sign, so only the API is exposed, which is the layer an attacker would use.

**Evidence:** Response body quoted above; balance 120 before, 125 after.

---

### BUG-03: Clicking Place Bet more than once places and charges duplicate bets

**Severity:** Critical

**Reproduction steps**

1. Open the application; note the balance from `GET /api/balance` (108.00 in this run).
2. Click `1` on Monaco vs Lyon and enter stake `3`.
3. Double-click **Place Bet**.
4. Watch the network requests and close the receipts that appear.
5. `GET /api/balance`.

**Expected:** The button is disabled while it shows "Placing..." (spec 2.3: in-progress state resolving to one final outcome). One request, one bet, one receipt; balance 105.00.

**Actual:** The button shows "Placing..." but stays clickable. Two `POST /api/place-bet` requests were sent about one second apart, both returned 200 (balances 105 and 102), and the balance ended at 102.00. A triple click with stake 2 sent three requests and charged 6.00 (114 to 108). Each extra bet produces its own receipt, which pops up after the previous one is closed, with a different Bet ID (#B-14671, #B-19280, #B-49910 for the triple click). The server-side `409 bet_in_progress` guard does not help because the UI sends the requests one after another, not at the same time.

**Business impact:** Customers are charged several times for a bet they meant to place once. Double-clicking a slow button is ordinary behaviour, so this will happen in normal use and leads to refund requests and chargebacks. There is no idempotency key, so the backend cannot tell a duplicate from a deliberate second bet.

**Evidence:** [03-extra-receipt-from-duplicate-submission.jpg](evidence/03-extra-receipt-from-duplicate-submission.jpg): a receipt for an earlier €2.00 duplicate (#B-19280) appearing on top of a new, unrelated €3.00 bet slip.

---

### BUG-04: Past matches are listed under "Upcoming Football Matches" and bets on them are accepted

**Severity:** High

**Reproduction steps**

1. Open the application on 11 October 2026 with no filters.
2. Look at the first entry: Premier League, Manchester Utd vs Chelsea, Fri 27 Feb, badge "PAST".
3. Click its `1` button (2.45), enter stake `1`, click **Place Bet**.
4. Alternatively `POST /api/place-bet` with `{"matchId":"premier-league-manutd-chelsea","selection":"HOME","stake":1}`.

**Expected:** Only upcoming matches are listed and bettable (spec section 1 and business rules: "Upcoming/Pre-match events only"). The API rejects a bet on a match whose kickoff has passed.

**Actual:** 83 of the 103 matches returned by `GET /api/matches` have a `kickoffDate` before the current date (the earliest is 2026-02-27). The UI lists them with a "PAST" badge, so the application knows they are in the past, yet their odds buttons work. The bet in step 3 was accepted with receipt #B-17610, and the API call in step 4 returns 200.

**Business impact:** Bets can be placed on matches whose result is already known. Depending on how settlement treats them this is either guaranteed winnings for the customer or void bets and support work; either way it is the kind of exposure a pre-match product must not have. Rated High rather than Critical only because settlement is outside this application; with live settlement it would be Critical.

**Evidence:** [06-past-matches-in-upcoming-list.jpg](evidence/06-past-matches-in-upcoming-list.jpg).

---

### BUG-05: Balance in the header and bet slip is not updated after a bet is placed

**Severity:** High

**Reproduction steps**

1. Open the application. Header and bet slip show "Balance: €120.00".
2. Place a €10.00 bet on any match and close the receipt.
3. Compare the header and bet slip balance with `GET /api/balance`.
4. Reload the page.

**Expected:** After step 2 the header and the bet slip both show €110.00 (spec 2.3: "On success: stake is deducted"; the balance is shared across the header and the bet slip).

**Actual:** The API returns 110.00, and the `place-bet` response itself contains `"balance":110`, but the header and the bet slip keep showing €120.00 through any number of bets. Only a page reload shows the real balance.

Because the bet slip validates the stake against this stale figure, the "Insufficient balance" check stops working after the first bet. Starting from 20.00: bet 20.00 (API balance 0.00, UI still €20.00), bet 20.00 again with no warning, and the API balance is -20.00. This is BUG-01 reachable by an ordinary user through the UI.

**Business impact:** Customers see money they have already spent and are allowed to keep betting with it. They discover the real balance only after a reload, which reads as money disappearing and is a direct trust and complaint issue.

**Evidence:** [05-stale-ui-balance-vs-api.jpg](evidence/05-stale-ui-balance-vs-api.jpg): header and bet slip show €20.00 while the API (overlay added by the tester) reports -20.00.

---

### BUG-06: Receipt shows the wrong potential payout (stake x 2 instead of stake x odds)

**Severity:** High

**Reproduction steps**

1. Click `1` on Monaco vs Lyon (2.15) and enter stake `10`. The bet slip shows potential payout €21.50.
2. Click **Place Bet** and read "Potential Payout" on the receipt.

**Expected:** €21.50, the value shown on the bet slip and returned by the API (`"payout":21.5`).

**Actual:** €20.00. The receipt ignores the odds and shows stake x 2 every time:

| Stake | Odds | Bet slip / API | Receipt |
|---|---|---|---|
| 10.00 | 2.15 | 21.50 | 20.00 |
| 5.00 | 4.25 | 21.25 | 10.00 |
| 100.00 | 3.35 | 335.00 | 200.00 |
| 20.00 | 3.35 | 67.00 | 40.00 |

**Business impact:** The receipt is the customer's proof of the bet. It contradicts the amount they accepted on the bet slip, understating the payout above odds of 2.00 and overstating it below. That guarantees disputes at settlement, and where the receipt overstates the payout the customer has written evidence for the higher amount.

**Evidence:** [01-bet-slip-before-placement.jpg](evidence/01-bet-slip-before-placement.jpg) (€21.50) and [02-receipt-wrong-payout-and-team-order.jpg](evidence/02-receipt-wrong-payout-and-team-order.jpg) (€20.00) for the same bet; [04-receipt-payout-not-stake-times-odds.jpg](evidence/04-receipt-payout-not-stake-times-odds.jpg) (stake €20.00 at 3.35 shown as €40.00).

---

### BUG-07: Receipt shows the teams in reversed order

**Severity:** High

**Reproduction steps**

1. Place any bet, for example on Monaco vs Lyon.
2. Read the "Match" line of the receipt.

**Expected:** "Monaco vs Lyon". The home team is always listed first and this convention carries through to the receipt (domain notes, Match Ordering).

**Actual:** "Lyon vs Monaco". Reproduced on every bet: "Sevilla vs Real Madrid" for Real Madrid vs Sevilla, "Chelsea vs Manchester Utd" for Manchester Utd vs Chelsea.

**Business impact:** Home and away define what outcomes `1` and `2` mean. With the teams swapped and no selection shown (BUG-11), a customer who backed the home side reads the receipt as a bet on the other team. The receipt cannot be relied on as a record of the bet.

**Evidence:** [02-receipt-wrong-payout-and-team-order.jpg](evidence/02-receipt-wrong-payout-and-team-order.jpg).

---

### BUG-08: Reset reports a balance of 125.50 but the stored balance is 120.00

**Severity:** High

**Reproduction steps**

1. `POST /api/reset-balance`.
2. `GET /api/balance`.

**Expected:** Both return the initial balance of 125.50 (spec 5.3: "Response body and persisted state must be consistent after reset"; the domain notes state the balance starts at €125.50).

**Actual:** Step 1 returns `{"message":"Balance reset successfully","balance":125.5,"currency":"EUR"}`. Step 2 returns `{"balance":120,"currency":"EUR"}`. Reproduced on every reset; the UI also shows €120.00 after a reset.

**Business impact:** The API reports a balance that is not the one it stored, a €5.50 discrepancy on the account's starting funds. Any client or test that trusts the response starts from a wrong figure. Whether 125.50 or 120.00 is the intended value needs a product decision; today one of the two is wrong.

**Evidence:** Response bodies quoted above.

---

### BUG-09: `POST /api/place-bet` returns currency "USD"

**Severity:** Medium

**Reproduction steps:** Place any valid bet through the API or the UI and read `currency` in the response.

**Expected:** `"currency":"EUR"` (spec business rules and the 200 response definition).

**Actual:** Every successful response contains `"currency":"USD"`, while `GET /api/balance` and `POST /api/reset-balance` return `"EUR"` for the same account.

**Business impact:** The amounts are euros but are labelled as dollars. The UI hard-codes the € sign so customers do not see it today, but any consumer of the API (a mobile client, reporting, reconciliation) would record the bet in the wrong currency.

**Evidence:** `{"message":"Bet placed successfully",...,"payout":21.5,"balance":110,"currency":"USD"}`.

---

### BUG-10: API payout is cut off instead of rounded, and can differ from the bet slip by one cent

**Severity:** Medium

**Reproduction steps**

1. In the UI select Monaco vs Lyon `1` (2.15) and enter stake `3`. The bet slip shows €6.45.
2. Place the bet and read `payout` in the `place-bet` response.

**Expected:** 6.45 (3 x 2.15 is exactly 6.45).

**Actual:** `"payout":6.44`. Other examples: 10.10 x 2.15 = 21.715 returns 21.71; 96.57 x 2.15 = 207.6255 returns 207.62. The pattern matches binary floating-point arithmetic followed by truncation (3 x 2.15 evaluates to 6.4499999...). The bet slip has the same habit for half cents: 1.50 x 2.15 = 3.225 is shown as €3.22.

**Business impact:** The customer can be offered one payout and recorded another, always one cent lower. The amount is small per bet but it is systematic and in the operator's favour, which is hard to defend to a regulator. The spec should state the rounding rule and money should be calculated in decimal or integer cents.

**Evidence:** Response `{"stake":3,"odds":2.15,"payout":6.44,...}` against €6.45 on the bet slip.

---

### BUG-11: Receipt does not show the selection

**Severity:** Medium

**Reproduction steps:** Place any bet and review the receipt.

**Expected:** The receipt lists Bet ID, match, **selection**, stake, odds, potential payout and timestamp (spec 2.4).

**Actual:** There is no selection (Home / Draw / Away) anywhere on the receipt. Combined with BUG-07 the receipt does not identify what was bet on. The timestamp is also only "Today, 20:53", with no date, so a saved receipt cannot be dated.

**Business impact:** The customer has no record of which outcome they backed, which weakens the receipt as evidence in any dispute.

**Evidence:** [02-receipt-wrong-payout-and-team-order.jpg](evidence/02-receipt-wrong-payout-and-team-order.jpg).

---

### BUG-12: Odds filter drops matches priced exactly at the minimum of the range

**Severity:** Medium

**Reproduction steps**

1. Open the Odds filter, set Min `1.35` and Max `1.35`, click **Apply**.
2. Repeat with Min `2.00`, Max `3.00`.
3. Repeat with Min `5.00`, Max `10.00`.

**Expected:** Ranges are inclusive at both ends (spec 2.6). Step 1 lists PSG vs Marseille (home price 1.35). Steps 2 and 3 list every match with a price inside the range, which is 73 and 12 matches according to `GET /api/matches`.

**Actual:** The maximum is inclusive (1.00 to 1.35 lists PSG vs Marseille) but the minimum is not. Step 1 lists nothing. Step 2 lists 69 matches; the four missing ones (for example Napoli vs Lazio, home 2.00) qualify only through a price of exactly 2.00. Step 3 lists 10; missing are Atletico Madrid vs Valencia (away 5.00) and PSG vs Marseille, which is dropped because its draw price is exactly 5.00 even though its away price of 7.50 is well inside the range.

**Business impact:** Matches at round-number prices such as 2.00, which is where customers naturally set a range, are silently hidden, so bettable events are not found.

**Evidence:** Counts above compared with the API data; label reads "Odds: 1.35 - 1.35" over an empty list.

---

### BUG-13: Odds filter accepts an invalid range (min greater than max) without feedback

**Severity:** Medium

**Reproduction steps:** Open the Odds filter, set Min `3.00` and Max `2.00`, click **Apply**.

**Expected:** The range is rejected with clear feedback (spec 2.6) and the list is unchanged.

**Actual:** The filter is applied. The label reads "Odds: 3.00 - 2.00" and the match list is completely empty, with no error and no "no matches" message.

**Business impact:** A simple input slip leaves the customer with a blank page and no explanation, which looks like an outage.

**Evidence:** Label "Odds: 3.00 - 2.00", 0 match cards rendered.

---

### BUG-14: `GET /api/place-bet` returns 200 with an empty object instead of 405

**Severity:** Medium

**Reproduction steps:** Send `GET /api/place-bet` with a valid `x-user-id`.

**Expected:** `405 method_not_allowed` (spec 4.3 and Swagger). The other endpoints behave correctly: `PUT /api/place-bet`, `GET /api/reset-balance`, `POST /api/matches` and `DELETE /api/balance` all return 405.

**Actual:** `200 {}`.

**Business impact:** No bet is placed, so there is no financial effect, but a success status for an unsupported call misleads API clients and monitoring, and suggests the route has an unintended handler.

**Evidence:** Status 200, body `{}`.

---

### BUG-15: Malformed JSON body returns 500 instead of 400

**Severity:** Medium

**Reproduction steps:** `POST /api/place-bet` with header `content-type: application/json` and the body `{"matchId": "x", ` (truncated JSON).

**Expected:** `400 {"error":"invalid_json","message":"Malformed JSON body."}` as documented in Swagger and required by spec 4.3.

**Actual:** `500 {"error":"internal_server_error","message":"Unable to process request."}`. Non-object bodies (`[1,2,3]`, `null`, `42`) are handled correctly with 400 `invalid_request`.

**Business impact:** A client-side mistake is reported as a server fault. That pollutes error-rate monitoring and alerting, and tells integrators to retry a request that can never succeed.

**Evidence:** Response body quoted above; the balance was unchanged.

---

### BUG-16: "Showing N matches" counter ignores the active filters

**Severity:** Low

**Reproduction steps:** Apply any date or odds filter, for example the single day 18/10/2026.

**Expected:** The counter shows the number of matches listed (1).

**Actual:** It always reads "Showing 103 matches", including when 69, 3, 1 or 0 matches are listed.

**Business impact:** Misleading information; with an empty result (BUG-13) the counter claims 103 matches are showing.

**Evidence:** Counter text against the number of match cards rendered.

---

### BUG-17: Date filter "Cancel" keeps the unapplied date in the filter label

**Severity:** Low

**Reproduction steps**

1. Apply the range 14/10/2026 to 22/10/2026 (three matches listed).
2. Reopen the date filter, click day 28, then click **Cancel**.

**Expected:** Cancel discards the change; the label still shows the applied range, 14/10/2026 to 22/10/2026.

**Actual:** The label changes to "Date: 28/10/2026" as soon as the day is clicked and stays that way after Cancel, while the list still shows the three matches from 14 to 22 October. Label and list disagree until the filter is applied or reset.

**Business impact:** The customer cannot tell which filter is actually in effect.

**Evidence:** Label "Date: 28/10/2026" with matches dated 14, 18 and 22 October listed.

---

### BUG-18: Bet slip does not show the available balance while a selection is active

**Severity:** Low

**Reproduction steps:** Note "Balance: €120.00" in the empty bet slip, then click any odds button.

**Expected:** The bet slip shows the entered stake, the available balance and the potential payout (spec 2.2).

**Actual:** The balance line is replaced by "Remove All". With a selection active the bet slip shows stake and payout only; the balance is visible only in the page header.

**Business impact:** Minor: the customer has to look away from the bet slip to check what they can afford.

**Evidence:** [01-bet-slip-before-placement.jpg](evidence/01-bet-slip-before-placement.jpg).

---

## Exploratory checks that passed

Recorded so the next tester does not repeat them without reason.

- **Authentication:** a request without `x-user-id` returns 401 `missing_user_id` on all four endpoints, as does an empty or blank value; an unknown id returns 401 `invalid_user_id`. Opening the UI without `user-id` shows "Unauthorized" and no matches.
- **Match and selection validation:** missing, empty, blank, numeric or `null` `matchId` returns 422 `invalid_match_id`; an unknown id returns 422 `invalid_match`. Missing, lower-case, padded, numeric, `null` or unknown `selection` returns 422 `invalid_selection`. No balance change in any case.
- **Odds mapping:** HOME, DRAW and AWAY each return the correct price for the match (checked on Real Madrid vs Sevilla, 1.55 / 4.25 / 6.00).
- **Extra request fields** (`odds`, `payout`, `balance`, `userId`, `currency`) are ignored; the server uses its own odds.
- **Concurrent API requests:** two simultaneous `place-bet` calls give one 200 and one 409 `bet_in_progress` (three runs out of three).
- **Selection handling:** clicking another outcome or another match replaces the selection and clears the stake; "Remove All" and the per-selection X both empty the bet slip.
- **UI stake messages:** "Minimum stake is €1.00", "Maximum stake is €100.00" and "Insufficient balance" appear at the right boundaries when the page balance is fresh; the field accepts digits, one decimal separator and two decimals only.
- **Error modal:** no placement failed on its own during the session, so a failure was simulated by stubbing the `place-bet` response with HTTP 500 in the browser. The modal matches spec 2.5 (title, explanatory text, Rebet and Close). Rebet closed the modal, retried once and produced a receipt with a single charge; Close and X both closed the modal and cleared the selection and stake; no money was taken for the failed attempt.
- **Date filter:** a single day and an inclusive range (14 to 22 October returned the matches on the 14th, 18th and 22nd) both work.

## Observations and questions for the product owner

These are not filed as defects because the specification does not settle them.

1. **Minimum stake.** Section 3 and the UI copy say €1.00; the validation table in 4.1 says "Minimum €1.01". The application accepts 1.00 on both layers. Which is intended?
2. **Bet ID.** The `place-bet` response contains no bet identifier, so the "#B-12345" on the receipt appears to be generated in the browser. If so it cannot be used to look a bet up. Should the API issue the id?
3. **Lock under heavier concurrency.** With five simultaneous requests, two were accepted and three got 409. The two successes may simply have been processed one after the other, but it is worth a targeted test with tooling that controls timing.
4. **Retry safety.** Rebet resends the same request with no idempotency key. If the first request actually succeeded but the response was lost, Rebet would place a second bet.
5. **Odds filter semantics.** The filter appears to keep a match if any of its three prices is in range; the spec does not say whether that or "all prices" is intended. The slider also stops at 10.00 although odds up to 1000.00 are allowed.
6. **Kickoff label.** The match three days ahead is labelled with a weekday only ("Wednesday") while all others show a date ("Sun 18 Oct"), and no match shows a kickoff time, although spec 2.1 asks for a date/time label.
7. **Empty body.** `POST /api/place-bet` with no body returns 422 `invalid_match_id` rather than a 400 for a missing payload.
