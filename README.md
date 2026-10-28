# ES-hackathon

Local workspace for the [ES Consulting Grok Bot Hackathon 2026](https://hack.esconsulting.io/).

## Connectors (Cursor MCP)

Project MCP config is in [`.cursor/mcp.json`](.cursor/mcp.json). After opening this folder in Cursor, enable these servers if they are not already on:

| Server | Mission | Auth |
| --- | --- | --- |
| `viewer` | All — publish to [view.esconsulting.io/view](https://view.esconsulting.io/view) | `Authorization: Bearer MCP_VIEW` |
| `bio` | 1 — Helen CoS (email, calendar, transcripts) | `Authorization: Bearer HelenMCP` |
| `eshack` | 2 — AtScale supply-chain / ops data | user `es-hackathon` / `Hackathon2026` |
| `primer` | 3 — Primer3 referee tools | none |

If AtScale shows a sign-in card, use the username and password above.

## Links

- Hub: https://hack.esconsulting.io/
- Agenda: https://hack.esconsulting.io/welcome
- Slides: https://hack.esconsulting.io/present
- AtScale guide: https://hack.esconsulting.io/AtScale
- Share guide: https://hack.esconsulting.io/share
- Slack bot (human): https://hack.esconsulting.io/slackbot
- Slack invite: https://join.slack.com/t/esconsultingh-bkk4135/shared_invite/zt-4exed8sow-unKQTmfKjHwSpQtnJ~d9AA

Slack bot setup still needs a bot name, a Grok/Cursor webhook routine, and Slack app tokens. Say if you want that wired next.
