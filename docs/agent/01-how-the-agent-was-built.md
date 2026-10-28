# 01. How the agent was built

## 1. The three parts

| Part | Where it lives | Built as | Status (27 October) |
| --- | --- | --- | --- |
| The tool: `propose_refund` | `parmana-agent-studio-mcp` on Vercel, from `examples/razorpay-agent-studio/mcp.ts` | Code | Deployed. Answers refusals end to end (Observed) |
| The Parmana API | `parmana-api-real` on Vercel, from `packages/api` | Code | Serving production (Observed) |
| The agent | Razorpay Agent Studio, test mode | Configured in the builder | Not built. No agent exists |

The tool is the only part the agent can reach in Parmana. Nothing in Agent Studio calls Parmana until the agent exists and Razorpay registers the tool.

## 2. Why the tool is a server and not a script

Agent Studio calls tools over the Model Context Protocol (MCP). Agent Studio's custom-connector path is not documented, so the tool is an MCP server. It speaks JSON-RPC and offers one tool, `propose_refund`. Razorpay has to register the server as a custom connector before the agent can call it. Until then the agent has no working tool. (Configured in Agent Studio; the README in `examples/razorpay-agent-studio/` records the same limit.)

## 3. The tool, as built

Code: `examples/razorpay-agent-studio/mcp.ts`, `agent.ts`.

- **Name and inputs.** `propose_refund(paymentId, amountPaise, purpose?, approval?)`. The schema requires `paymentId` and `amountPaise`, and allows no other fields.
- **Authentication to the tool.** A bearer token, `AGENT_STUDIO_TOKEN`. Compared in constant time. Missing or wrong: `401`, body `{"error":"unauthorized"}`.
- **Message shape.** The body must be one JSON-RPC message. Anything else: `400`.
- **Input check.** `validateRefundInput` requires a `pay_` id of 6 to 40 letters or digits, and an amount that is a positive whole number of paise. A failure returns an error text to the agent and calls nothing.
- **Decision.** `requestRefund` reads the caller identity and the policy in effect, builds a business transaction, and calls Parmana's `execute`. If Parmana rejects it, the tool reads the refusal record.
- **Answer.** One JSON text block:
  - Refused: `{"status":"REFUSED","businessTransactionId","rule","reason"}`. Missing rule or reason is shown as `not recorded`.
  - Approved: `{"status":"APPROVED","businessTransactionId","razorpay"}`, where `razorpay` is the endpoint's result. The refund id is inside it.
- **A request that fails after its id is created** (a timeout, a connection failure, or an error from Parmana). Fixed on branch `fix/agent-tool-failure-transaction-id` (commit `6198f0b`), not yet deployed. Returns a tool error `{"status":"NOT_COMPLETED","businessTransactionId","message"}`, and the message says not to send the request again. Before the fix, it was a bare `500` with the JSON-RPC error `The refund proposal did not complete.`, and the id was only in the logs.
- **Anything else.** Any other unexpected exception becomes `500` with the same JSON-RPC error. The real message is written to the server log only.

Code note: `requestRefund` catches only `ExecutionRejectedError`. Every other error is rethrown, so a timeout or a connection failure reaches the tool's catch and becomes a `500`. It is never returned as a refusal or an approval.

## 4. The instructions

These are the instructions given to the agent in Agent Studio (Configured; text from `examples/razorpay-agent-studio/README.md`, step 3):

> You propose refunds of Razorpay payments with the `propose_refund` tool only. Pass the payment id (`pay_...`) and the amount in paise (100 is ₹1). Never invent an approval or a payment id. If the answer is REFUSED, report the rule and reason to the user and do nothing else. Do not retry a refused request without a new approval.

The description of the agent's job, recorded in the builder (Configured):

> When a support agent asks to refund a Razorpay payment, the agent sends the payment id, the amount in paise, and the manager's signed approval to Parmana. It reports the refund id if approved, or the rule and reason if refused, and then stops. No refund happens without Parmana's approval.

The builder rules that were chosen but are not in the code (Configured):

- Check that the payment id and amount are present. If either is missing, ask for it and stop.
- Hold any request above ₹500 for a person on the team, and do not send it to Parmana.
- If Parmana approves but no refund id comes back, stop and mark the refund "not confirmed".
- If Parmana's answer has no clear status, stop with "no clear decision", and refund nothing.

These rules run in Agent Studio, so they are only as good as the instructions and the builder configuration. Check them on the dashboard, and record the configured text in `02`.

## 5. The example runs (Configured, Agent Studio builder)

The builder ran four example runs on sample data. Results on 27 October:

| Example | Result | What it shows |
| --- | --- | --- |
| ₹1 request with approval | Stopped with "no clear decision" and refunded nothing | The stop path works, but it does not test an approval |
| ₹750 request | Held for the team, not sent | The ₹500 hold works in the builder |
| Payment id missing | Asked for the payment id and amount | The input check works in the builder |
| Parmana approves, Parmana refuses | Not run | These need a real Parmana answer |

## 6. What is built, and what is not

Built and observed:

- The tool's authentication, input checks, refusal and approval answers (Code, Observed).
- Parmana's refusal of a request with no grant, with a rule and reason (Observed).
- The refusal record's `businessTransactionId` at the top level (Observed).

Built but not run through the agent:

- The approved path through the tool (Code). It has not been run with a real grant and a real approval through the MCP server.

Not built:

- The Agent Studio agent itself.
- Razorpay's registration of the connector.
- An event receiver for the support tool's requests.
- Daily limits and the ₹1,00,00,000 backstop.

## 7. Versions and where they were set

| Setting | Value | Where |
| --- | --- | --- |
| Per-request grant limit | 500 paise (₹5), valid until 3 November 2026 | Parmana grant `dbdd05f1-...`, approved 27 October (Observed) |
| Draft production policy limit | ₹5,000 per refund, not approved | `examples/razorpay-refund-manager-approved/policy.json` (Code) |
| Builder hold | Above ₹500 held for a person | Agent Studio builder (Configured) |
| Mode | Test mode | Razorpay dashboard, and the endpoint refuses `rzp_live_` keys (Code) |

The three limits differ on purpose: the grant is the one that is enforced today, the builder hold is a second check on the agent's side, and the draft policy is not in force. Keep them consistent when any one changes.
