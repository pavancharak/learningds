# Razorpay refund agent under Parmana: end to end

Status as of 27 October 2026. Written for the operator, the meeting on 29 October, and whoever picks this up next.

Every claim carries one label:

- **Code:** read in the repository, with the file named.
- **Observed:** seen in a live call on 27 October 2026.
- **Reported:** from the operator's status letter of 23 October 2026, not checked in this repository.
- **Open:** not built, not tested, or not decided.

Nothing here contains a key, token or secret value. Secrets are named by where they live, never by what they are.

---

## 1. What the system does, in one paragraph

A support agent asks for a refund of one Razorpay payment. Parmana decides whether the refund may go out. Two things must be true: the agent holds an authority grant for `razorpay:refund` within its limit, and a manager has signed an approval for that payment and that amount. Only when Parmana releases the refund does a small endpoint call Razorpay's refund API, in test mode. Parmana never holds a Razorpay credential. Every decision, approved or refused, leaves a record that Parmana signs. (**Code:** `examples/razorpay-refund/README.md`, "How it fits together".)

---

## 2. The parts and who holds what

| Part | Where it runs | What it holds | What it is for |
|---|---|---|---|
| Support tool or backend (trigger) | Your side. Not built | Nothing secret. Sends payment id, amount and the signed approval | Starts a refund request. **Open:** which system does this (Freshdesk, Zendesk or in-house) is not decided |
| Agent Studio agent | Razorpay Agent Studio, test mode | Nothing secret | Turns a request into one call to the tool. **Observed:** not built yet. No agent exists on the dashboard as of 27 October |
| Parmana MCP server | Vercel project `parmana-agent-studio-mcp` (`https://parmana-agent-studio-mcp.vercel.app/api/mcp`) | Bearer token `AGENT_STUDIO_TOKEN` (who may call the tool) and `PARMANA_API_KEY` (the agent's own key to Parmana) | Exposes one tool, `propose_refund`, and calls Parmana for the decision. **Code:** `examples/razorpay-agent-studio/mcp.ts` |
| Parmana API | Vercel project `parmana-api-real` (`https://parmana-api-real.vercel.app`) | `PARMANA_API_KEYS`: the hashed caller list (hashes only, not keys). Policies, grants, approvals, the kill switch, trust records | Authenticates callers, evaluates policy, releases refunds, records every decision. **Code:** `docs/runbooks/KEY-ROTATION.md`, `packages/api` |
| Refund endpoint | Vercel project `parmana-razorpay-demo` (`https://parmana-razorpay-demo.vercel.app/api/refund`) | `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` (test keys), and Parmana's public key | Verifies Parmana's signed release, then refunds in Razorpay. **Code:** `examples/razorpay-refund/endpoint.ts`, `razorpay.ts` |
| Razorpay | Razorpay test mode | Its own account | Holds the payment and makes the refund. The dashboard is the record of the refund |

**The three identities that matter:**

- **The agent** (`razorpay-refund-agent`): a SERVICE caller with capability `razorpay:refund` only. It can ask; it cannot approve.
- **The manager approver** (`manager-pavan` in the demo): signs the approval with the approver key. The agent never holds this key.
- **The checker and maker** (`pavancharak`, `maker-pavan`): propose and approve policy, connector and grant changes, using step-up keys. They also hold the kill-switch keys.

---

## 3. The end-to-end flow

### 3.1 Target flow (how it is designed to run)

```
Support tool ──(payment id, amount in paise, signed approval)──▶ Agent Studio agent
                                                                    │ (one tool call)
                                                                    ▼
                                              Parmana MCP server (bearer token check)
                                                                    │ validate input (pay_..., whole paise > 0)
                                                                    │ read Parmana's policy in effect
                                                                    │ build the business transaction
                                                                    ▼
                                              Parmana API: execute (caller key check)
                                                                    │ kill switch off?
                                                                    │ caller holds razorpay:refund in force?
                                                                    │ amount within grant limit?
                                                                    │ signed manager approval for this payment and amount?
                                                                    │ approval unused?
                                                                    ├── any "no" ─▶ signed refusal record ─▶ REFUSED back to the agent
                                                                    ▼ all "yes"
                                              signed release (audience = endpoint URL, expiry)
                                                                    ▼
                                              Refund endpoint: verify signature, audience, expiry, test mode
                                                                    │ look up its own refund by receipt = businessTransactionId
                                                                    │ none found: POST /v1/payments/{id}/refund
                                                                    ▼
                                              Razorpay refund (receipt = businessTransactionId)
                                                                    ▼
                                              endpoint answers with the refund ─▶ Parmana records it ─▶ APPROVED back to the agent
```

**Code:** the agent's decision logic is `examples/razorpay-refund-agent/agent.ts` (`requestRefund`). The endpoint's checks are in `endpoint.ts` and `razorpay.ts` (signature, audience, expiry, `receipt` lookup, `assertTestMode`).

### 3.2 What was actually run (observed 27 October)

Only the refusal path has been run through the deployed MCP server and the deployed Parmana API:

1. A request with no authority grant for `razorpay-refund-agent` reached Parmana and was refused. The agent received `status: REFUSED`, `rule: authority-not-authorized`, the reason, and a `businessTransactionId`. No refund was created in Razorpay (the dashboard shows only the 23 October refund).

The approved path has not been run through the MCP server. It is reported as run on 23 October through the demo scripts (`send.ts`), against the demo endpoint, in test mode (see section 8).

---

## 4. How the agent is built

### 4.1 In Razorpay Agent Studio

**Observed:** Agent Studio's builder (Build Agents, Beta, Test Mode on) takes a plain-language description and generates the agent. No agent has been generated yet.

The builder description we settled on:

> When a support agent asks to refund a Razorpay payment, the agent sends the payment id, the amount in paise, and the manager's signed approval to Parmana. It reports the refund id if approved, or the rule and reason if refused, and then stops. No refund happens without Parmana's approval.

The instructions the agent should carry (from `examples/razorpay-agent-studio/README.md`, step 3):

> You propose refunds of Razorpay payments with the `propose_refund` tool only. Pass the payment id (`pay_...`) and the amount in paise (100 is ₹1). Never invent an approval or a payment id. If the answer is REFUSED, report the rule and reason to the user and do nothing else. Do not retry a refused request without a new approval.

### 4.2 The tool

The tool is `propose_refund(paymentId, amountPaise, purpose?, approval?)`. **Code:** `mcp.ts` (tool definition, lines 34 to 60).

- `paymentId` must match `pay_` followed by 6 to 40 letters or digits.
- `amountPaise` must be a positive whole number. 100 is ₹1.
- `approval` is the manager's signed approval, passed through unchanged.

**Open:** the tool is not attached to the agent. Agent Studio's custom-connector path is not documented by Razorpay. Razorpay has to register the MCP server as a connector before the agent can call it. The README says this can take about a week.

### 4.3 Agent Studio's test state

**Reported (27 October):** the example runs on the builder's sample data:

| Example | Result |
|---|---|
| ₹1 request with approval | Passed as a safe stop: the simulated call returned no answer, so the agent stopped with "no clear decision" and refunded nothing |
| ₹750 request | Passed: held for the team, not sent to Parmana |
| Payment id missing | Passed: asked for the payment id and amount |
| Parmana approves | Not run, needs a real Parmana answer |
| Parmana refuses | Not run in Agent Studio. The same refusal was seen from the MCP server directly (section 3.2) |

**Observed:** the agent's refusal reading matches the MCP server's real answer, which has `status`, `rule`, `reason` and `businessTransactionId` at the top level (`mcp.ts` lines 100 to 115).

The agent is **not verified and not switched on**. It stays that way until the approved and refused cases pass against real Parmana answers through Agent Studio.

---

## 5. How the agent talks to Parmana

### 5.1 The MCP server (the agent's door)

**Code:** `examples/razorpay-agent-studio/mcp.ts`.

1. **Bearer check.** Every request needs `Authorization: Bearer <AGENT_STUDIO_TOKEN>`. A missing or wrong token gets `401`. **Observed:** `401` for a blank token and for a 43-character value left in an old file. The body of that `401` was not captured.
2. **Protocol.** It speaks JSON-RPC: `initialize`, `tools/list`, `tools/call`. Only `propose_refund` is offered.
3. **Input check.** `validateRefundInput` rejects a bad payment id or amount before anything is sent. It returns `isError` text, not a refund.
4. **Decision.** It calls `requestRefund` (`agent.ts`), which:
   - validates the input again,
   - reads the caller identity (`client.caller()`),
   - reads the policy in effect for `razorpay:refund` (`client.policyInEffect`),
   - builds a business transaction with `managerApproved` set only if an approval is present,
   - calls `client.execute`. If Parmana rejects it, it reads the refusal record (`client.refusalRecord`).
5. **Answer.** It returns one JSON text block:
   - Refused: `{ status: "REFUSED", businessTransactionId, rule, reason }`. `rule` and `reason` come from Parmana's record, and show "not recorded" if missing.
   - Approved: `{ status: "APPROVED", businessTransactionId, razorpay }`, where `razorpay` is the endpoint's result. The refund id is inside that result.
6. **Errors.** Any exception inside the handler becomes `500` with JSON-RPC error `-32603` "The refund proposal did not complete." The server log line shows the real message.

### 5.2 The caller identity

The MCP server authenticates to Parmana with `PARMANA_API_KEY`. Parmana looks the key up by its hash in `PARMANA_API_KEYS` and applies that caller's capabilities.

- **Observed (27 October):** when the key was missing or its hash was not in the live list, Parmana answered `401 authentication required`, and the MCP server returned `500` with `mcp_error: authentication required`.
- **Observed:** after the new key was loaded, the same request returned `REFUSED` with `authority-not-authorized`. This shows the caller was recognised and then failed the grant check.

### 5.3 The three refusal stages

Parmana checks in this order, and each stage gives a different answer:

| Stage | Example answer | Seen |
|---|---|---|
| Caller known and allowed | `401 authentication required` | Yes (27 Oct) |
| Kill switch | `503 KILL_SWITCH_ACTIVE` (the MCP server shows it as `500`) | Yes (27 Oct) |
| Authority grant in force and within limit | `REFUSED`, `authority-not-authorized`, or `NOT_AUTHORIZED` | Yes for "no grant" (27 Oct). The over-limit case was run by the demo (23 Oct) |
| Manager approval for this payment and amount | `REFUSED`, `reject-manager-approval-required` | Demo, 23 Oct |
| Approval unused | `REFUSED`, `signal-state-verification-violation` | Demo, 23 Oct |

---

## 6. How Parmana talks to the backend

### 6.1 Parmana's API

**Code:** `packages/api`, routes such as `execute.ts`, `kill-switch.ts`, `policies.ts`, `transactions.ts`.

- `POST /execute` takes a business transaction and returns a signed execution record (approved) or a refusal (`403 POLICY_DENIED` for policy refusals, covered by `refusal-record.integration.test.ts`).
- `GET /trust-records/{businessTransactionId}` returns the signed record for a transaction. Use it to check a timed-out request before any resend.
- `GET /policies` requires a caller key. It is the health check the runbooks use.
- `GET /kill-switch/status` is readable by any valid key. `POST /kill-switch/trip` needs `kill-switch:trip`. `POST /kill-switch/reset` needs `kill-switch:reset`, and a reset is two requests by two different keys.

### 6.2 The release to the endpoint

**Code:** `examples/razorpay-refund/endpoint.ts`, `build-endpoint.ts`.

- The endpoint is registered as the connector for `razorpay:refund` with a fixed URL. A release made for any other URL is refused.
- The release is signed by Parmana. The endpoint checks the signature, that the audience is its own URL, and that the release has not expired (`tests/razorpay-refund.test.ts` covers each).
- `build-endpoint.ts` writes Parmana's public key and the endpoint's own URL into the bundle, so a deployment must be built with the URL it will be served from.

### 6.3 What Parmana stores

Each decision produces a record. Approved records carry the execution result. Refused records carry the rule and reason. Both are signed and can be verified offline with the public key only (`scripts/verify-trust-record.ts`).

---

## 7. How Parmana connects to Razorpay

**Code:** `examples/razorpay-refund/razorpay.ts`, `endpoint.ts`.

1. **Test mode is enforced.** `assertTestMode` refuses to start when `RAZORPAY_KEY_ID` does not start with `rzp_test_`. The test `assertTestMode({ keyId: "rzp_live_..." })` throws.
2. **Credentials stay with the endpoint.** The endpoint reads `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` from its own Vercel environment. Parmana never sees them.
3. **One refund per decision.** The endpoint lists existing refunds for the payment. If one already has `receipt` equal to the release's `businessTransactionId`, it returns that refund with `alreadyRefunded: true` and does not refund again. Otherwise it creates the refund with that receipt and a note carrying the same id.
4. **The answer.** The endpoint returns `refundId`, `paymentId`, `amount`, `status`, `receipt`, `alreadyRefunded` and `mode: "test"`.

**Reported (23 October):** one refund, ₹1, `rfnd_TrPyItqZ6h7Dgo` on `pay_TrPtgJ3RVnzzFi`, status processed, receipt `4346a484-f85d-4c3c-bc61-2f416aabd586`. The letter says the three refused cases created no refunds. The refund list for 20 to 27 October shows only that one refund (checked on 27 October).

**Open:** the production endpoint is not separate from the demo. The Agent Studio path needs the endpoint and the policy agreed with Razorpay, and that is the subject of the 29 October meeting.

---

## 8. Records of the runs

| Date | What | Result | Source |
|---|---|---|---|
| 23 Oct | Demo: ₹1 approved, refunded | `rfnd_TrPyItqZ6h7Dgo`, processed | Status letter (reported) |
| 23 Oct | Demo: no approval | Refused by policy | Status letter (reported) |
| 23 Oct | Demo: ₹8 above grant | `NOT_AUTHORIZED` | Status letter (reported) |
| 23 Oct | Demo: approval reused | Refused, already used | Status letter (reported) |
| 27 Oct | MCP, live: no grant | `REFUSED`, `authority-not-authorized`, `businessTransactionId` present | Observed |
| 27 Oct | Razorpay refund list, 20 to 27 Oct | One refund, the 23 Oct ₹1 | Observed |
| 27 Oct | Probe workflow after the new probe key | Green | Observed |

---

## 9. Secrets map

Names only. Values are never written in this document, in chat, or in the repository.

| Name | Where it lives | Used by | Notes |
|---|---|---|---|
| `AGENT_STUDIO_TOKEN` | Vercel, `parmana-agent-studio-mcp`, production. Password manager. Encrypted copy in `parmana-secrets-fresh\agent-studio-token.dpapi` | MCP server (checks the bearer token) | Rotated 27 Oct |
| `PARMANA_API_KEY` | Vercel, `parmana-agent-studio-mcp`, production | MCP server, as the agent `razorpay-refund-agent` | Rotated 27 Oct. Its hash is in the live list |
| `PARMANA_API_KEYS` | Vercel, `parmana-api-real`, production. Holds hashes only | Parmana API | Redeployed 27 Oct. Built and validated with `parseApiKeys` |
| Caller keys (`pavancharak`, `maker-pavan`, `kill-switch-probe`, `razorpay-refund-agent`) | Password manager. Encrypted copies (`*.key.dpapi`) in `parmana-secrets-fresh` | Operators, the probe, the agent | Verified against their entries on 27 Oct |
| Checker step-up private key | Password manager. `checker.step-up.private.pem` in `parmana-secrets-fresh` | Policy and grant approvals | Plain PEM on disk; restrict the folder |
| `PARMANA_PROBE_KEY` | GitHub Actions secret, repository `pavancharak/parmana-core` | Workflow `kill-switch-probe.yml`, every 15 minutes | Updated 27 Oct. The probe run passed |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Vercel, `parmana-razorpay-demo`, production. Razorpay test keys | Refund endpoint | Test keys only; the endpoint refuses `rzp_live_` |

**Stale and removed on 27 Oct:** the GitHub secret `PARMANA_API_KEYS`, which no workflow read, and the old files in `parmana-secrets`.

---

## 10. Meeting preparation: 29 October, 5:00 to 5:30 PM IST

Attendees from Razorpay: Aravinth Kumar P K (organiser), Vaidehee Joshi, Riya Parikh. From Parmana: the founder.

Decisions to agree, and what each one changes:

| # | Decision | Current state | Option | What it changes in the system |
|---|---|---|---|---|
| 1 | Trigger: how a refund request reaches the agent | Designed as a direct call from Agent Studio. No event receiver exists | Keep the direct call, or build a signed-event receiver | Keep: nothing new. Event receiver: build and test it, then decide on idempotency and retries |
| 2 | Manager approval: required per refund or not | Required for every refund (`reject-manager-approval-required`) | Keep it, or allow refunds up to a set amount without it | Change needs a new policy version, approved by the checker |
| 3 | Per-request limit | Test grant ₹5 (500 paise, 7 days). Draft policy allows ₹5,000 per refund, not approved. Backstop of ₹1,00,00,000 not built | Agree the live grant limit, approve or change the draft policy, agree the backstop | A new grant, approved, and a policy version if the limit is in the policy |
| 4 | Refusal status | Policy refusal is `403 POLICY_DENIED` (tested). The `NOT_AUTHORIZED` status is not tested | Confirm 403, or give a different status for over-limit | Test the over-limit case on a running server before promising a status |
| 5 | Connector registration | MCP server deployed. Razorpay must register it. No agent built | Razorpay names who builds the agent and registers the connector | Nothing in Parmana until the agent exists |

Points not to claim:

- Do not describe the agent as live, or as having run through Agent Studio. It has not.
- Do not describe ₹5,000 as the live limit. It is a draft.
- Do not promise a status code for the over-limit case until it is tested.
- Do not say the 23 October run went through Agent Studio. It went through Parmana's API and the demo scripts.
- Do not share a key, a token or a step-up key, in chat, in email or in a meeting.

---

## 11. What is still open

1. **The approved path through the MCP server.** Needs the agent's grant approved and a manager's signed approval for a real test payment. The approved answer's shape, including where the refund id sits in `razorpay`, is still unconfirmed.
2. **Agent Studio registration.** Razorpay must register the MCP server. Until then the agent cannot call Parmana.
3. **Trigger.** Not decided, and no event receiver exists.
4. **The production endpoint.** The demo endpoint is test-mode only. A production endpoint, its policy and its limits are not built.
5. **The over-limit status.** `NOT_AUTHORIZED` has no test that shows its HTTP status.
6. **Daily limits.** Designed, not built.
7. **Order-system check.** The demo does not check eligibility against an order system.
8. **The `businessTransactionId` fallback.** The agent looks inside `razorpay` if the top level is missing. Harmless, but it can be removed.

---

## 12. What went wrong on 27 October, and how to avoid it

These were real problems in this rotation, in order of cost.

1. **Production was down for a while.** A new deployment started with a `PARMANA_API_KEYS` value that was not a JSON array, and every request returned `500 FUNCTION_INVOCATION_FAILED`. Fix: promote the last good deployment first, then read the Runtime Logs error. The error text was `PARMANA_API_KEYS is not valid JSON`.
   - **Avoid:** build the list with `ConvertTo-Json -InputObject`, validate with `parseApiKeys`, and upload from a file with `cmd /c "... < file"`. Piping a string through PowerShell into `vercel env add` did not store the value intact.
2. **Vercel removes first, then adds.** `env rm` ran without a successful `env add`, leaving the variable missing. Any redeploy then fails.
   - **Avoid:** run `rm` and `add` back to back, and check `vercel env ls` before any redeploy.
3. **A deployment can go live even when it crashes.** A redeploy that is Ready at the platform level can still fail at startup and become production.
   - **Avoid:** after every redeploy, check `/policies` at once. Keep the last good deployment's URL ready to promote.
4. **A false match.** A hash check compared two empty values and printed `MATCHES`. Caught because `$global:Keys` and `$live` were empty.
   - **Avoid:** fail when either side is empty. Check the length of every value before comparing.
5. **Read-Host and pasted lines.** When lines were pasted into a block with prompts, the prompts took the pasted text as answers, so keys were not saved to the password manager.
   - **Avoid:** run one key block at a time, press Enter only after saving.
6. **`$dir`, `$link` and `$token` disappear between windows.** Commands ran with empty values, and one request went out with an empty token.
   - **Avoid:** set variables in the same window as the command, and check their lengths first.
7. **Paths with spaces in `cmd /c`.** `--cwd` with a path containing a space split the path.
   - **Avoid:** run `Push-Location` to the folder and use the file redirect.
8. **Plain-text key files.** Keys were saved as `.key.txt` files, which is what the rotation removed.
   - **Avoid:** keep keys in the password manager, or in files encrypted to the Windows account with `ConvertFrom-SecureString`.
9. **A key that is not in the live list is a lock-out, not a leak.** If the list is uploaded before the key is saved, that caller cannot authenticate, and its key has to be regenerated.
   - **Avoid:** verify each saved key against its own entry before the upload.

---

## 13. The checks that prove it works

Run them in this order. Each has an expected result, and a failure stops the next step.

1. `GET /policies` with no key returns `401 authentication required` (the API is up and checking keys).
2. Each caller's key, typed from the password manager, hashes to its entry's `keyHash` (`MATCHES`).
3. The probe workflow is green on a manual run.
4. The MCP refusal request returns `REFUSED` with `rule`, `reason` and `businessTransactionId` at the top level, and Razorpay shows no new refund on the payment.
5. After the grant is approved: the over-limit request returns `REFUSED` with `NOT_AUTHORIZED`.
6. After a manager's approval and a real test payment: the approved answer returns `APPROVED` with a refund id, and Razorpay shows exactly one refund whose receipt equals the `businessTransactionId`.
7. Repeat the approval: `REFUSED`, and still exactly one refund.

Do not switch the agent on for real refunds until checks 1 to 7 have passed on the real deployed services, and the trigger is decided.
