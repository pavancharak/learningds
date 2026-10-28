# 05. Grant and approval

Two different things make a refund allowed. Both are needed, and neither can stand in for the other.

1. **The agent's authority grant.** Says the caller `razorpay-refund-agent` may request `razorpay:refund`, up to a limit, until a date. Set by a maker and approved by a checker.
2. **A manager's signed approval.** Says a person approves this refund for this payment and this amount. Signed by an approver's private key, and trusted only if the approver is registered as an approval issuer.

## 1. The grant (done, 27 October)

| Field | Value |
| --- | --- |
| Change id | `dbdd05f1-dac6-4477-86f3-4fa4ca528e82` |
| Caller | `razorpay-refund-agent` |
| Capability | `razorpay:refund` |
| Limit | `parameters.amount` up to 500 paise (₹5) per request |
| Valid until | `2026-11-03T18:43:24.396Z` |
| Proposed by | `maker-pavan` |
| Approved by | `pavancharak`, with a step-up authorization |
| Status | `APPROVED` (observed) |

**Commands** (see `02`, section N):

```powershell
npx tsx $g propose-grant --caller-id razorpay-refund-agent --capability razorpay:refund --max-amount 500 --valid-days 7
npx tsx $g approve --kind grant --id $gid --step-up-key-file "$dir\checker.step-up.private.pem" --step-up-key-id pavancharak
```

The approval printed the change and waited for the word `APPROVE`. The first attempt, with lower-case `approve`, stopped without approving anything. The second, with `APPROVE`, returned `Status: APPROVED`.

**Note:** the 23 October grant was issued to `razorpay-demo-agent`. It does not cover this agent's key, and it expired after 7 days.

## 2. The manager's approval (not done)

### What the code requires (verified in the repository)

From `packages/api/src/routes/approval-issuers.ts` and `packages/api/src/auth/governanceGuards.ts`:

- **Adding an issuer.** `POST /approval-issuers/changes` with `{"action":"add","approverId","keyId","publicKeyPem","reason"}`. `approverId` and `keyId` match `^[A-Za-z0-9._-]{1,128}$`. The key must be Ed25519.
- **Approving the addition.** `POST /approval-issuers/changes/<id>/approve` with `{"stepUpAuthorization": ...}`. The authorization is bound to the change id and the action `approve`, and is valid for 120 seconds.
- **Who may do each.** Both routes need a human caller (`USER`). The proposer may not approve their own change.
- **Startup.** A trusted issuer whose key does not parse, is not Ed25519, or appears twice stops the server from starting.

### Where the approver key comes from

`scripts/generate-approver-key.ts` (in the repository) generates the pair. It is run by the approver, on their own machine:

```powershell
npx tsx scripts/generate-approver-key.ts --approver-id manager-pavan --key-id manager-pavan-key-1 --out-dir "$env:USERPROFILE\parmana-approver"
```

It writes `manager-pavan__manager-pavan-key-1.private.pem` and `...public.pem`. The private key stays with the approver. The public key is what gets registered.

### What is missing

- The approver's private key does not exist on this machine (checked 27 October: `NO DOES NOT EXIST`).
- `examples/live-checks/governance.ts` has no commands for approval issuers. It handles policies, connectors, sources and grants only. The approval routes can be called directly, but the step-up signature has to be built the same way the helper builds it.

### Decision recorded

On 27 October the operator accepted route 1 (add issuer support to the helper, on a branch, reviewed before use) and accepted that for this test the manager, maker and checker are the same person, with no second-person review. The runbook's checklist asks for that review, so this is a recorded deviation. It is acceptable for the test only. A real manager's approval needs a second person.

### Work started and paused

A change to `governance.ts` was started on `feat/approval-issuers-governance` (based on `origin/main`, commit `33bdd58`). It added the types, a request helper for the issuer routes, and the `issuer` kind to the approve command. It was reverted before it was committed, so the branch is clean. The steps to finish it are in `06`.

## 3. Why the approval matters

A refund is allowed only if the grant covers it and a valid, unused approval for this payment and amount is present. The approval is checked against the payment's current state, so a reused or stale approval is refused. A refund of ₹1 with no approval is refused by policy, as the 23 October demo showed.

## Update, 27 October (later): the approver is registered

- The approver key `manager-pavan-key-2` was generated fresh. The 11 October pair was not used.
- It was proposed by `maker-pavan` (change `f85a497a-139e-447a-94fb-e6ea01874f50`) and approved by `pavancharak` with the step-up key. Status `APPROVED`.
- The helper gained `propose-issuer` and `approve-issuer` (branch `feat/approval-issuers-governance`, commit `84374e1`, pull request #168).
- The single-person deviation applies here too: the same person proposed and approved, under two keys. It is recorded in `07`.
- Still open: the check in `07`, section 5, and a real approval signed by this key.
