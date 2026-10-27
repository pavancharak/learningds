# 08. Meeting discussion points: Parmana and Razorpay Agent Studio

Meeting: Thursday 29 October 2026, 5:00 to 5:30 PM IST, Google Meet.
Razorpay: Aravinth Kumar P K (organiser), Vaidehee Joshi, Riya Parikh.
Parmana: the founder.

This file is internal preparation. It is not for sending to Razorpay as it stands.

## 1. The goal of the meeting

Agree five things, and record the answer to each:

1. How a refund request reaches the agent.
2. Whether refunds up to a set amount may skip the manager's approval.
3. The per-request limit, and the backstop.
4. The refusal status for the over-limit case.
5. Who on Razorpay's side builds the agent and registers the connector.

## 2. Where things stand (as of 27 October)

What is working:

- **Refusals end to end through the deployed services.** A request with no authority grant reaches Parmana, and comes back `REFUSED` with the rule (`authority-not-authorized`), the reason and a transaction id. Nothing is refunded.
- **The agent has a grant.** `razorpay-refund-agent` may request `razorpay:refund` up to ₹5 per request, valid until 3 November 2026.
- **The manager's approver is registered.** A signing key for manager approvals is trusted by Parmana. It was registered by a maker and approved by a checker, on 27 October.
- **The probe runs** on schedule, with its own key.
- **Keys are rotated and verified.** The old keys were revoked, and every current key is checked against its entry.

What is not working or not built:

- **The Agent Studio agent has not been built.** Nothing in Agent Studio calls Parmana.
- **Razorpay has not registered the MCP server** as a custom connector. Razorpay has said this can take about a week.
- **The approved refund has not run through the MCP tool.** The only refunds on record are from 23 October, through the demo scripts, in test mode.
- **The support tool that sends requests is not decided.** No event receiver exists.

## 3. The five decisions

### Decision 1: how a refund request reaches the agent

- **Current design:** Agent Studio's agent calls Parmana's tool directly, once per request.
- **Alternative:** the support tool sends a signed event, and Parmana receives it. This needs an event receiver, which is not built.
- **What to ask Razorpay:** can the agent be triggered from the support tool, or does a person start each request in Agent Studio?
- **Our position to take:** the direct call is simpler, and it's what is built. The event route needs a receiver, its own tests, and an agreed signing key.

### Decision 2: manager approval, required or not

- **Current design:** every refund needs a signed manager approval for that payment and amount. The policy refuses without one.
- **Alternative:** refunds up to a set amount go through without an approval.
- **What to ask Razorpay:** what is the business rule? Is the approval needed for every refund, or only above a threshold?
- **Our position to take:** keep the approval until Razorpay has a written rule. Any change is a new policy version, approved by a checker, so it takes a few days, not minutes.

### Decision 3: the per-request limit

- **Current state:** the test grant is ₹5 per request. A draft policy allows ₹5,000 per refund, and it is not approved. The ₹1,00,00,000 backstop is not built.
- **What to ask Razorpay:** what is the largest refund the agent should ever request? Is there a daily cap?
- **Our position to take:** start at ₹5 in test mode. Raise it only with a written limit, a new grant, and a policy change. Daily limits are designed, not built.

### Decision 4: the refusal status for an over-limit request

- **Current state:** a policy refusal returns `403 POLICY_DENIED`, which is tested in the API. The status for an over-grant refusal (`NOT_AUTHORIZED`) is not tested.
- **What to ask Razorpay:** does the integration need `403` specifically, or is any refusal status with a reason acceptable?
- **Our position to take:** do not promise a status for the over-limit case until it has been run on a live server.

### Decision 5: who builds the agent and registers the connector

- **Current state:** the MCP server is deployed. No agent exists in Agent Studio. Razorpay must register the server as a custom connector.
- **What to ask Razorpay:** who builds the agent, who registers the connector, and by when?
- **Our position to take:** the agent's instructions and the tool definition are ready (see `docs/razorpay-journey/02` and `01`). Parmana can support the test run once the connector is registered.

## 4. What to show, and how

- Show the refusal path: a live request, the refusal, and no refund in Razorpay. This is observed, not reported.
- Describe the approved path as designed, and say it has not yet run through the agent.
- Show the 23 October demo as reported: test mode, through the demo scripts, not through Agent Studio.

## 5. What not to say

- Do not say the agent is live, or that it has run through Agent Studio.
- Do not describe ₹5,000 as the live limit. It is a draft.
- Do not promise a status code for the over-limit case.
- Do not share a key, a token, a step-up key or an approver key, in the meeting, in chat or in email.
- Do not describe the approver as independent. The same person proposed and approved it for this test.

## 6. Record the answers

| # | Question | Razorpay's answer | Agreed by | Date |
| --- | --- | --- | --- | --- |
| 1 | How requests reach the agent | | | |
| 2 | Manager approval required or not | | | |
| 3 | Per-request limit and backstop | | | |
| 4 | Refusal status for over-limit | | | |
| 5 | Who builds the agent and registers the connector | | | |

## 7. After the meeting

1. Write the agreed answers into the table above, with the date and the names.
2. Send Razorpay a written summary of the answers, and update the status letter's section 4.
3. Run the over-limit request on a live server, to confirm the status code before anyone promises it.
4. Agree the date for the first test refund, which is a ₹1 refund on one of Razorpay's own test payments.
