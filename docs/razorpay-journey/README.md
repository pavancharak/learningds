# Razorpay refund agent: the full journey

This folder records how the Razorpay refund agent under Parmana was built, deployed and tested, from October 2026, including what failed and how it was fixed. It is written so someone who was not there can repeat each step, or understand why it was not repeated.

Start with `01-timeline-and-state.md` for the overview, then read the other files as needed.

| File | What it covers |
| --- | --- |
| [01-timeline-and-state.md](01-timeline-and-state.md) | Day-by-day timeline, and the state of each part at the end of 27 October 2026 |
| [02-commands-and-outcomes.md](02-commands-and-outcomes.md) | Every command that mattered, what it printed, and what it meant |
| [03-incidents-and-fixes.md](03-incidents-and-fixes.md) | Each failure: the symptom, the cause, the fix, and how to avoid it next time |
| [04-keys-and-secrets.md](04-keys-and-secrets.md) | Every key and token: its name, where it is stored, what uses it. Names only, never values |
| [05-grant-and-approval.md](05-grant-and-approval.md) | The authority grant, the manager approval, and the approver-key gap |
| [06-open-items-and-next-steps.md](06-open-items-and-next-steps.md) | What is still not proven, and the order to do it in |
| [07-approver-registration.md](07-approver-registration.md) | Registering the manager's approver key: why, each command, the outcomes, and the checks |
| [08-meeting-discussion-points.md](08-meeting-discussion-points.md) | Internal prep for the 29 October meeting with Razorpay: the five decisions, what to say and not say, and where to record answers |

## How to read the labels

Each claim is one of:

- **Observed:** seen in a command's output during this journey. The output is quoted in `02`.
- **Reported:** taken from the operator's status letter of 23 October 2026, not checked again.
- **Code:** read in a repository, with the file named.
- **Open:** not done, not tested, or not decided.

## What is never in these files

No key, token, password, step-up private key, or connection string. Where a secret is mentioned, it is named by its file or variable, and its value is in the password manager.

Identifiers that are not secrets are recorded: change ids, business transaction ids, refund ids, payment ids, deployment URLs and caller ids.
