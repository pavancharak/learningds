# The Razorpay refund agent

How the agent was built, how it behaves in each scenario, including when it gets stuck, why it behaves that way, and how a stuck state is resolved.

| File | What it covers |
| --- | --- |
| [01-how-the-agent-was-built.md](01-how-the-agent-was-built.md) | The parts, the builder inputs, the tool, the instructions, and what was built versus configured |
| [02-behaviour-by-scenario.md](02-behaviour-by-scenario.md) | Every scenario the agent can meet, with the response it gives and where that response comes from |
| [03-stuck-states-why-and-how-to-resolve.md](03-stuck-states-why-and-how-to-resolve.md) | Each way the agent can get stuck, why it stops, what a person does, and how to tell it is resolved |

## Labels

- **Code:** in a repository file, with the file named. This is what the program does.
- **Configured:** set in Agent Studio's builder by hand, so it is not in any repository file. It can differ from what is written here, and it must be checked on the dashboard.
- **Observed:** seen in a live call on 27 October 2026.
- **Open:** not built, not tested, or not decided.

## Where the agent's behaviour is decided

The agent's behaviour comes from three places, and they must agree:

1. **The Agent Studio agent** (configured). It decides what to say to the support agent and when to stop. Its instructions are in `01`.
2. **The MCP tool** (code, `examples/razorpay-agent-studio/mcp.ts`). It checks the request, calls Parmana, and returns one of a small set of answers.
3. **Parmana** (code, `packages/api`). It decides whether the refund is allowed, and records why.

If the agent does something the code does not return, look first at the instructions in Agent Studio.

## Not in this folder

No key, token, step-up key or secret value. Names only, and only where they are used.
