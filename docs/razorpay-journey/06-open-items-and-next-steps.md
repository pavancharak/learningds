# 06. Open items and next steps

Ordered by what blocks what. Each item says what "done" means.

## What is proven

| Claim | Evidence |
| --- | --- |
| The Parmana API serves production with the current caller list | `/policies` returns `401` without a key (observed, 27 October) |
| The MCP server authenticates to Parmana as the agent | The refusal test returns `REFUSED` with a `businessTransactionId` (observed) |
| Parmana refuses a request from an agent with no grant, and reports the rule | `authority-not-authorized` (observed) |
| The probe runs with its key | Green on a manual run (observed) |
| The grant for `razorpay-refund-agent` is in force | `APPROVED` (observed), valid until 3 November |
| A refund request with no approval is refused by policy | Demo, 23 October (reported) |
| A ₹1 refund with approval reached Razorpay in test mode | Demo, 23 October (reported). The refund list confirms the refund exists |
| The refund endpoint refuses live keys and checks Parmana's signature | Code (`examples/razorpay-refund/`), with tests |

## What is not proven

| Claim | Why it is open |
| --- | --- |
| The approved refund goes through the MCP tool and Razorpay | Needs an approver key, a registered issuer, and a captured test payment |
| The approved answer's shape, including where the refund id is | Never observed through the MCP server |
| Agent Studio can call the tool | No agent is built. Razorpay must register the MCP server as a connector |
| The `NOT_AUTHORIZED` status is 403 | Not tested |
| The support tool sends the requests | Not decided. No event receiver exists |

## Order of work

### 1. Approver key (operator, own machine)

- **Done when:** `manager-pavan__manager-pavan-key-1.public.pem` exists, and the private key is in the password manager.
- **Command:** `npx tsx scripts/generate-approver-key.ts --approver-id manager-pavan --key-id manager-pavan-key-1 --out-dir "$env:USERPROFILE\parmana-approver"`.
- **Gate:** none. It is local and reversible.

### 2. Helper support for approval issuers (code, on a branch)

- **Done when:** `governance.ts` has `propose-issuer` and `approve --kind issuer`, both pass the build and any tests, and the change is reviewed.
- **Work:** finish the paused change on `feat/approval-issuers-governance`. Add a `propose-issuer` command that posts `{"action":"add",...}` with the public key file. Add `issuer` to the approve command, which lists pending issuer changes, signs the step-up for the change id with action `approve`, and posts `{"stepUpAuthorization": ...}`.
- **Gate:** a pull request on `parmana-core`, merged before use against production. Needs push access to the repository from this session.

### 3. Register the approver (production change)

- **Done when:** the issuer change is `APPROVED`, and `GET /approval-issuers/changes` shows the key as trusted.
- **Steps:** maker proposes the add with the public key; checker approves with step-up.
- **Gate:** your explicit go-ahead, per change.

### 4. Captured test payment (operator, Razorpay test mode)

- **Done when:** a `pay_...` id with status `captured` is recorded here.
- **Note:** the refund must not exceed the grant's ₹5, so use ₹1 (100 paise).

### 5. The manager's approval for the payment

- **Done when:** a signed approval file exists for that payment and 100 paise, produced with the approver key.
- **Gate:** the approver's own action, on their machine.

### 6. The approved refund through the MCP tool

- **Done when:** the MCP call returns `APPROVED` with a refund id under `razorpay`, and Razorpay shows one refund whose receipt equals the `businessTransactionId`.
- **Record:** the answer's exact shape, including where the refund id sits, in `02`.

### 7. The repeated approval

- **Done when:** the same approval sent again returns `REFUSED`, and Razorpay still shows one refund.

### 8. Pass on the record

- **Done when:** steps 6 and 7 are recorded in `02`, and the Agent Studio notes in `01` are updated.

## Decisions for the 29 October meeting

These are recorded in the meeting brief. Not decided by this journey:

1. How a refund request reaches the agent (direct call, or signed events from the support tool).
2. Whether refunds up to a set amount may skip the manager's approval.
3. The live per-request limit (₹5 test grant, ₹5,000 draft, ₹1,00,00,000 backstop).
4. The refusal status for the over-limit case.
5. Who on Razorpay's side registers the connector.

## Rules to keep

- No live refund without a recorded approval, a grant in force, and a passing check.
- No production change without a written go-ahead for that change.
- Two different people for every approval in production. The test-only exception applies to this journey alone.

## Update, 27 October (later)

- Step 1 (approver key) is done: `manager-pavan-key-2`, generated fresh.
- Step 2 (helper support) is done: pull request #168, with `propose-issuer` and `approve-issuer`.
- Step 3 (register the approver) is done: change `f85a497a-139e-447a-94fb-e6ea01874f50`, `APPROVED`. The verification in `07`, section 5, is not yet run.
- The next gate is step 5: a real approval signed by this key for a captured test payment. It needs your go-ahead, and a payment id.
