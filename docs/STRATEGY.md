# Strategy and Recommendations

## Why these two tests

I could only automate two, so I picked by risk first and then by how reliably the test can run.

**UI: place a single bet end to end.** This is the journey every customer takes, and it is the only test that sees all the parts together: match list, bet slip, the place-bet call, the receipt and the balance. What it really checks is that the three views of the same bet agree. That is exactly where I found the worst UI defects (wrong payout on the receipt, teams reversed, balance not updated), and they are the kind of thing you stop noticing when you check by eye for the tenth time. It is also a stable flow to automate: one path, ids on the elements, data taken from the API.

**API: a stake above the balance is rejected.** Of all the validation rules this is the one that protects money, and only the server can really enforce it. The UI check can be skipped by calling the API, and it also relies on a balance that turned out to be stale. The test sits on the boundary (one cent over), checks the response and the stored balance, needs no browser and finishes in a few seconds.

Between them they cover both layers, one happy path and one negative case, and the two things the business can least afford: a customer who cannot place a correct bet, and a customer who can place one they cannot pay for.

Other candidates I considered:

| Candidate | Why not now |
|---|---|
| Stake min / max / precision matrix on the API | Next in line. Cheap, and ideal for `parametrize`. |
| Past matches must be rejected by the API | Also next. Simple once BUG-04 is confirmed as a bug. |
| Double click on Place Bet | Depends on click timing in the UI, so it would be flaky. |
| Error modal and Rebet | The app gives no way to force a failure. |
| Filters | Lower risk, and expensive to drive through a date picker. |

## What I left manual

- **Exploratory testing around placement.** Fast clicks, odd inputs, changing selection mid-flow. Most of my bug list came from this, not from the scripted steps. Automation only repeats what somebody already thought of.
- **Duplicate submission.** High risk, but a UI test for it would depend on timing. The proper fix is an idempotency key on the API, and then it becomes an easy API test. Until then I would check it by hand each release.
- **Failure path (error modal, Rebet, Close).** I had to stub the response in the browser to see it at all. It belongs in a component test with a mocked API, not in a black-box E2E test.
- **Filters.** Medium risk and a lot of UI plumbing for little return. The filter logic itself should be unit tested by the developers.
- **How the receipt and messages read.** Whether a receipt is complete and clear is a human judgement. I noticed the missing selection by reading the receipt against the spec.
- **Anything the spec does not settle.** Minimum stake 1.00 or 1.01, starting balance 125.50 or 120.00, how payout is rounded. These need an answer before a check can be pass or fail.

## Recommendations if this grows

**1. Put most of the coverage on the API and keep the UI suite small.**
Nearly every rule in the spec is a validation rule, and all three Critical bugs were on the API. I would cover the whole validation table with parametrised API tests (status, error code, balance unchanged) and add contract tests against the OpenAPI file, which would have caught things like `currency: "USD"` and the 500 on malformed JSON for free. Loading state, double click, error modal and balance refresh fit best in component tests with a mocked API. That leaves three to five UI journeys end to end.

**2. Run it in CI with fast feedback.**
Lint and API tests on every pull request (under a minute), UI smoke on merge against a preview deployment, the full suite nightly. Publish the JUnit report and failure screenshots. Tests that fail because of a known bug should be marked as expected failures linked to the ticket, so the build stays green but the test starts failing loudly once the fix is in and the mark has to go. There is a manually triggered workflow in `.github/workflows/tests.yml` as a starting point.

**3. Make the test data controllable.**
This was the biggest practical limit:

- One shared account means tests cannot run in parallel and anyone using the same id can break a run. A throwaway user per test would fix that.
- There is no way to set a balance. My API test has to place a real 100.00 bet to get down to 20.00. A test-only endpoint would make setup one call.
- The match list uses real dates. 83 of 103 matches are already in the past and the rest will follow, so a test that needs an upcoming match will eventually find none. Matches should be seeded relative to today.
- A test switch to force a failed or slow placement would let the error and retry paths be tested properly.

**Spec questions I would raise first**

1. Minimum stake: 1.00 (section 3 and the UI text) or 1.01 (table 4.1)?
2. Starting balance: 125.50 or 120.00?
3. How is payout rounded? UI and API should use the same rule.
4. What status and error code should the API return for insufficient balance? Swagger only has it as an example.
5. Who creates the Bet ID? The API response does not contain one.
