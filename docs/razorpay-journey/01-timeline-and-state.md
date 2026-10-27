# 01. Timeline and state

## Timeline

### 23 October 2026: the demo refund (reported)

The operator ran the demo in Razorpay test mode, through Parmana's API and the demo scripts. The status letter sent to Razorpay on 23 October reports:

- A ₹1 refund was approved and processed: `rfnd_TrPyItqZ6h7Dgo` on `pay_TrPtgJ3RVnzzFi`. Its receipt was the transaction id `4346a484-f85d-4c3c-bc61-2f416aabd586`.
- A request with no manager approval was refused by policy.
- A ₹8 request, above the ₹5 grant, was refused as `NOT_AUTHORIZED`.
- Sending the same approval again was refused.

The demo grant (7 days, up to ₹5) was issued to `razorpay-demo-agent`, not to the agent that exists now.

**Not in the repository:** the run itself. Only the refund list, which we checked on 27 October, shows the one refund.

### 23 October: status letter and Agent Studio

- A status letter was sent to Razorpay describing the demo results and five open decisions.
- The MCP tool was deployed to Vercel as `parmana-agent-studio-mcp`.
- The letter said the Agent Studio tool was "deployed, not registered". On 27 October the operator confirmed that no agent had been built in Agent Studio. The letter's Agent Studio statements were corrected in the runbook and in a correction text. The letter itself has not been re-sent.

### 27 October 2026: the key rotation and its aftermath

This is the day most of the work happened. In order:

1. **Keys pasted into chat.** The `maker-pavan` and `pavancharak` keys were pasted into the conversation during a prompt. They were treated as exposed and rotated.
2. **The first rotation.** A new `PARMANA_API_KEYS` list was uploaded to `parmana-api-real`. Production returned `500 FUNCTION_INVOCATION_FAILED`. The Runtime Logs said `PARMANA_API_KEYS is not valid JSON`. The last good deployment was promoted, and the API was restored.
3. **The second rotation.** The list was rebuilt, uploaded through a file redirect, and redeployed. It served correctly, and `/policies` returned `401` without a key.
4. **The MCP key.** `PARMANA_API_KEY` was set on the MCP project. The MCP server returned `500` with `authentication required`, because the key was not in the live list.
5. **Kill switch.** Parmana's kill switch was on: `active true`, version 1, tripped by `operator-a` at 2026-10-27T10:06:39Z, reason `probe`. It was reset by two operators: `maker-pavan` started the reset, and `pavancharak` completed it. Status afterwards: `active false`, version 3.
6. **The refusal test.** The MCP tool returned `REFUSED`, rule `authority-not-authorized`, with a `businessTransactionId`. No refund appeared in Razorpay.
7. **The probe.** The GitHub secret `PARMANA_PROBE_KEY` was updated, the probe workflow was run by hand, and it passed (green).
8. **The rotation done properly.** All four caller keys were regenerated (`pavancharak` with a step-up key, `maker-pavan`, `kill-switch-probe`, `razorpay-refund-agent`). Each was verified against its own entry before the list was uploaded. The list was uploaded and the API redeployed. Production answered `401` to a request without a key.
9. **The agent key.** The agent's key was set on the MCP project and the MCP server was redeployed. The MCP token was rotated as well. The refusal test returned `REFUSED` with `authority-not-authorized`, which means the agent authenticated to Parmana.
10. **Cleanup.** The old files in `parmana-secrets` were deleted, and the stale GitHub secret `PARMANA_API_KEYS` was removed. Only the fresh copies remain in `parmana-secrets-fresh`.
11. **The new grant.** A grant for `razorpay-refund-agent` was proposed by `maker-pavan` and approved by `pavancharak`: change id `dbdd05f1-dac6-4477-86f3-4fa4ca528e82`, up to 500 paise per request, valid until 2026-11-03.
12. **Approver key gap.** The manager approver's key file does not exist on this machine. An approver has to be registered as an approval issuer before its signature is trusted. The helper script does not support issuers yet. A change to add that support was started and then paused, and it has not been committed.

### 27 October: learningds

A separate repository, `pavancharak/learningds`, was created for learning notes. The end-to-end document and this journey folder are in it. This is not part of the Razorpay system.

## State at the end of 27 October 2026

| Part | State | Evidence |
| --- | --- | --- |
| Parmana API `parmana-api-real` | Serving production. Its `PARMANA_API_KEYS` holds the four current callers. The promoted deployment is the one that serves | `/policies` returns `401` without a key (Observed) |
| Kill switch | Off, version 3 | Status check (Observed) |
| MCP server `parmana-agent-studio-mcp` | Deployed. Its bearer token and agent key are set | Refusal test returned `REFUSED` (Observed) |
| Agent `razorpay-refund-agent` | Authenticates to Parmana. Has a grant for `razorpay:refund`, up to ₹5, valid until 3 November | Grant status `APPROVED` (Observed) |
| Agent in Agent Studio | Not built | Operator confirmation, 27 October (Observed) |
| Probe | Running on schedule with the new key. Green on a manual run | Workflow run (Observed) |
| Razorpay | One refund in the 20–27 October range, from 23 October | Dashboard screenshot (Observed) |
| Approver key | Not created. No approval issuer registered | Filesystem check (Observed) |
| Approved refund through the MCP tool | Not run | Open |
| Trigger from the support tool | Not decided | Open |
