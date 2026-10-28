# 02. How the agent behaves, scenario by scenario

For each scenario: what the input looks like, what the agent does, what it tells the support agent, and where that comes from.

Source labels:

- **Code:** `mcp.ts`, `agent.ts` (in `examples/razorpay-agent-studio/`), or `packages/api` in `parmana-core`.
- **Configured:** the Agent Studio builder, which is not in the repository.
- **Observed:** a live call on 27 October 2026.

## A. Input problems (the agent checks before calling anything)

| # | Scenario | What the agent does | What it tells the support agent | Source |
| --- | --- | --- | --- | --- |
| A1 | Payment id missing | Asks for it. Calls nothing | "Please give me the payment id and amount." | Configured (builder). Observed in the example run |
| A2 | Amount missing | Asks for it. Calls nothing | Same, for the amount | Configured |
| A3 | Payment id not `pay_...` | The tool rejects it before calling Parmana | An error text naming the rule for the payment id | Code (`validateRefundInput`) |
| A4 | Amount not a positive whole number of paise | The tool rejects it before calling Parmana | "The amount must be a positive whole number of paise (100 is ₹1)." | Code |
| A5 | Amount above ₹500 | Holds the request for the team. Does not call Parmana | "This refund is held for the team." | Configured. Observed in the example run (held, not sent) |

Why these are checked first: a bad input should never reach Parmana, because that would create a record of a request nobody meant to make, and it costs a call.

## B. The tool's own failures (before any decision)

| # | Scenario | What the tool returns | What the agent should do | Source |
| --- | --- | --- | --- | --- |
| B1 | No bearer token, or wrong token | HTTP `401`, `{"error":"unauthorized"}` | Stop. Report that the tool is not authorised. Do not retry | Code (`mcp.ts`). The body was not observed on 27 October; the status was |
| B2 | Body is not one JSON-RPC message | HTTP `400` | Stop. This is a configuration fault | Code |
| B3 | The tool's handler throws (for example, Parmana's API is unreachable or rejects the agent's key) | HTTP `500`, JSON-RPC error `The refund proposal did not complete.` The real message is only in the server log | Stop. Do not retry, and report that the refund did not complete. A person checks the log | Code (`mcp.ts` lines 271 to 282). Observed: `authentication required` on 27 October |

Consequence: the support agent sees "did not complete" and nothing more. The reason is in the log, so a person has to read it.

## C. Parmana's decision

| # | Scenario | Parmana's answer | What the tool returns | What the agent says and does | Source |
| --- | --- | --- | --- | --- | --- |
| C1 | Approved: grant in force, within limit, valid approval | Execution record | `APPROVED`, `businessTransactionId`, `razorpay` | Reports the refund id from `razorpay`. Stops | Code. The refund id's exact field inside `razorpay` is **open** (not yet observed) |
| C2 | Approved, but no refund id in `razorpay` | Execution record without a refund id | `APPROVED`, no id | Stops. Says "approved, but no refund id was returned. Check Razorpay for a refund with receipt <transaction id> before doing anything else." Marks the refund "not confirmed" | Configured (builder). The tool returns what it has |
| C3 | Refused: no grant for the agent | Refusal record | `REFUSED`, `authority-not-authorized`, reason, `businessTransactionId` | Reports the rule and reason. Stops. No retry | Code. Observed on 27 October |
| C4 | Refused: no manager approval | Refusal record | `REFUSED`, `reject-manager-approval-required` | Same | Demo policy (Code, `examples/razorpay-refund/policy.json`). Reported 23 October |
| C5 | Refused: amount above the grant | Refusal | `REFUSED`, `NOT_AUTHORIZED` in the demo | Same | Demo (Reported 23 October). The HTTP status is **open** |
| C6 | Refused: the approval was already used | Refusal | `REFUSED`, `signal-state-verification-violation` | Same. A new approval is needed | Demo (Reported 23 October) |
| C7 | Refused: no rule or reason in the record | Refusal without rule or reason | `REFUSED` with `not recorded` | Reports `not recorded`. Stops | Code (`agent.ts` lines 105 and 106) |
| C8 | Answer has no status, or an unknown one | Anything else | Whatever the tool returned | Stops with "no clear decision". Refunds nothing | Configured (builder) |

## D. The kill switch and the platform

| # | Scenario | What happens | What the agent does | Source |
| --- | --- | --- | --- | --- |
| D1 | Kill switch on | Parmana refuses execution with `KILL_SWITCH_ACTIVE`. The MCP tool returns `500` and logs the code | Stops. Reports "did not complete". A person checks the switch | Observed on 27 October. Runbook: `503 KILL_SWITCH_ACTIVE` is expected while tripped |
| D2 | Parmana's API is down (startup failure) | `500 FUNCTION_INVOCATION_FAILED` on every request | Stops. Reports "did not complete" | Observed on 27 October (the rotation). Runbook section 1 |
| D3 | Parmana's API rejects the agent's key | The tool logs `authentication required` and returns `500` | Stops. A person checks the key on Vercel | Observed on 27 October |

## E. Timeouts and repeats

| # | Scenario | What is at risk | What the agent should do | Source |
| --- | --- | --- | --- | --- |
| E1 | The call times out, or the answer never arrives | The refund may have run | Do **not** send the request again. A person checks the record first | Runbook (`docs/runbooks/RAZORPAY-REFUND.md`, "If request 2 times out"). Code: `agent.ts` rethrows, so the tool returns `500` |
| E2 | The same approval is sent a second time | A second refund | Refused (C6). The approval is spent | Demo (Reported 23 October) |
| E3 | The same approved request is sent again to the endpoint | A duplicate Razorpay refund | The endpoint returns the existing refund, with `alreadyRefunded: true`, if it carries the same receipt | Code (`razorpay.ts`, lines 162 to 175) |

Gap: the tool does not return a `businessTransactionId` when it fails with a `500`, so a person cannot look up the record from the tool's answer. They have to find the transaction by the payment in the logs.

## F. What is not verified

- **How the endpoint behaves when Razorpay itself fails** (for example, a Razorpay `5xx`). The code path exists, but it has not been tested on the deployed endpoint in this journey. **Open.**
- **The HTTP status for a refusal over the grant.** **Open.**
- **Whether the agent actually follows the instructions in A to C.** The builder's example runs covered A1, A5 and the stop path only. **Open.**
