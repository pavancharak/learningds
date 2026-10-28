# 03. Stuck states: why, and how to resolve them

A stuck state is any point where the agent cannot finish a refund and must stop. Each one below says why the agent stops, what a person does, and how to tell it has been resolved.

The rule across all of them: **a stop is safe.** Nothing is refunded by a stop. The risk is the other way round, a person "fixing" a stop by sending the request again, which can double a refund or spend an approval.

## S1. Missing payment id or amount

- **Why it stops:** the request cannot be made without them. The agent asks, rather than inventing a value (Configured; the instruction "Never invent an approval or a payment id").
- **How to resolve:** the support agent gives the payment id (`pay_...`) and the amount in paise. The agent starts again with those values.
- **Resolved when:** the request has both values and passes the input check.

## S2. Input not valid (not `pay_...`, or amount not a whole number of paise)

- **Why it stops:** the tool's input check rejects it before Parmana is called (Code, `validateRefundInput`).
- **How to resolve:** correct the value. Check that the amount is in paise: ₹1 is `100`, not `1`.
- **Resolved when:** the tool accepts the request.

## S3. Above the team's hold (₹500)

- **Why it stops:** the builder holds any request above ₹500 for a person, and does not call Parmana (Configured). The hold protects against a large refund by mistake.
- **How to resolve:** a person decides. If the refund is wanted, the grant has to allow it, which is a separate grant change. A ₹5 grant does not allow a ₹500 request either.
- **Open:** where a held request is kept, and who sees it. The builder does not say. Decide this before go-live.
- **Resolved when:** the person has either rejected the request, or has a grant and approval that cover it, and sends it again as a new request.

## S4. Refused by Parmana, with a rule and a reason

- **Why it stops:** Parmana's policy said no. The agent reports the rule and the reason, and does not retry (Configured; the instruction "Do not retry a refused request without a new approval").
- **How to resolve, by rule:**
  - `authority-not-authorized`: the agent has no grant for `razorpay:refund`. A maker proposes a grant, a checker approves it (`02`, section N). Then the request can be sent again.
  - `reject-manager-approval-required`: no approval was attached. A manager signs one for this payment and amount, and it is sent with the request.
  - `NOT_AUTHORIZED` (over the grant): the amount is above the grant's limit. Either the request is made smaller, or the grant is changed. A manager's signature does not lift the limit (Reported 23 October).
  - `signal-state-verification-violation` (approval already used): the approval is spent. A new approval is needed.
- **Resolved when:** the cause for that rule is fixed, and a new request is made with the new approval or grant. Never resend the same request with the same approval.

## S5. "No clear decision", or no status in the answer

- **Why it stops:** the answer has no status the agent recognises. It refunds nothing (Configured).
- **How to resolve:** a person reads the answer. Look at the tool's log for the same call, and at Parmana's record for the transaction. The likely causes are a change in the answer's field names, or a tool that has not been deployed with its latest code.
- **Resolved when:** the answer has a recognised status, or the cause of the change is fixed in the tool or in the agent's configuration.

## S6. Approved, but no refund id came back

- **Why it stops:** the refund may have happened. The agent cannot confirm it, so it marks the refund "not confirmed" (Configured).
- **How to resolve:** check the Razorpay dashboard for a refund whose receipt equals the transaction id in the message. If one exists, record it against the request and close the case. If none exists, the refund did not happen. Escalate to the Parmana side. Do not send the approval again: it is spent.
- **Resolved when:** the refund is confirmed in Razorpay, or it is established that none was made and the case is handed over.

## S7. The tool returned `500`, or the request timed out

- **Why it stops:** an error that is not a refusal reaches the tool and becomes `500 The refund proposal did not complete.` The request may or may not have reached Parmana (Code, `agent.ts` and `mcp.ts`).
- **How to resolve:**
  1. Read the tool's log for the message: `vercel logs parmana-agent-studio-mcp.vercel.app --since 10m --json`.
  2. If the message is `authentication required`, the agent's key is not in Parmana's live list. See S9.
  3. If the message is `KILL_SWITCH_ACTIVE`, see S8.
  4. If the call reached Parmana, its record is under the transaction id. Read it with `GET /trust-records/<transaction id>` using a valid key. Do this before anything else.
  5. Check Razorpay for a refund on the payment with a receipt matching that id.
- **Do not** send the request again until steps 4 and 5 show that no refund was made, and a new approval exists if the old one was used.
- **Gap:** the tool does not return the transaction id on a `500`, so step 4 depends on finding the id in the logs. **Open:** return the id on failure, or log it in a form that can be searched.
- **Resolved when:** the cause in the log is fixed, and the refund has been confirmed or ruled out in Razorpay.

## S8. The kill switch is on

- **Why it stops:** Parmana refuses execution and approvals while the switch is tripped (Code, runbook `KILL-SWITCH-OPERATOR-GUIDE.md`). Observed on 27 October: the tool logged `KILL_SWITCH_ACTIVE`.
- **How to resolve:** check the switch with `GET /kill-switch/status` (any valid key). If it is on, the operators decide. A reset takes two operators, each with their own key, and the cause has to be written down first (`docs/runbooks/KILL-SWITCH-OPERATOR-GUIDE.md`). Do not reset it to make a refund go through.
- **Resolved when:** status shows `active: false`, and the cause is in the incident log.

## S9. Parmana does not recognise the agent's key

- **Why it stops:** the tool's key for Parmana is not in the live caller list (Observed on 27 October: `authentication required`).
- **How to resolve:** check the key on the MCP project against its entry. The entry is the source of truth. If they do not match, regenerate the key for `razorpay-refund-agent` and update it on Vercel, then redeploy. Follow `docs/runbooks/KEY-ROTATION.md`.
- **Resolved when:** the refusal test returns `REFUSED` with a rule and reason, not `500`.

## S10. Parmana's API itself is failing at startup

- **Why it stops:** the API cannot start, so every request returns `500 FUNCTION_INVOCATION_FAILED` (Observed on 27 October).
- **How to resolve:** promote the last good deployment at once (`vercel promote <url> --yes`). Then read the Runtime Logs error and fix the cause before deploying again. The usual cause was a bad `PARMANA_API_KEYS` value.
- **Resolved when:** `/policies` returns `401` without a key.

## S11. The tool's bearer token is wrong

- **Why it stops:** Agent Studio presents a token the tool does not accept, and the tool returns `401 {"error":"unauthorized"}` (Code).
- **How to resolve:** the token in Agent Studio must equal the `AGENT_STUDIO_TOKEN` on the MCP project. Rotate it if it is unknown or exposed, on both sides, then redeploy.
- **Resolved when:** the tool accepts the call.

## S12. Repeated attempts

- **Why it matters:** an agent that retries on its own can send the same refund many times, and a retry on an approved request uses an approval that is already spent.
- **The instructions today:** they forbid retrying a refused request. They do not forbid retrying a `500`.
- **How to resolve:** add to the builder instructions: "If the tool returns a 500 or a timeout, do not retry. Report that the refund did not complete, and stop."
- **Resolved when:** the instruction is in the builder, and a 500 has been tested to produce a stop.

## What to check after any stuck state is resolved

1. The agent's answer is the one expected for that scenario (see `02`).
2. Razorpay test mode shows the expected refunds, and no others, for the payment.
3. The record for the transaction in Parmana matches the answer.
4. The case is written down in the journey folder, with the cause and the fix.
