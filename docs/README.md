# OTIA Café documentation

Last verified: 2026-10-18.

## Start here

| Document | Purpose |
| --- | --- |
| [../README.md](../README.md) | Local setup, commands, service addresses and configuration |
| [architecture.md](architecture.md) | System structure, authentication, order/payment invariants and API map |
| [frontend.md](frontend.md) | Student, barista and admin frontend conventions and iPad testing |
| [security.md](security.md) | Backend security controls, known deployment limits and production checklist |
| [security-review-2026-10-18.md](security-review-2026-10-18.md) | Current Codex Security result, fixed findings, evidence and remaining production blockers |
| [deployment.md](deployment.md) | Test deployment, release steps, rollback and remote verification |
| [../GLOSSARY.md](../GLOSSARY.md) | Canonical Chinese/English product terminology |
| [adr/0001-yudao-java-backend.md](adr/0001-yudao-java-backend.md) | Why the product moved to the Yudao Java backend |
| [upstream.md](upstream.md) | Upstream repositories, pinned revisions and retained modules |
| [image-credits.md](image-credits.md) | Menu photo provenance and licensing |
| [OTIA-Cafe-项目书.docx](OTIA-Cafe-项目书.docx) | Product proposal and original requirements |

## Current environment

The documented remote environment is a **test deployment**:

- Student: `http://150.158.121.81:5001`
- Barista: `http://150.158.121.81:5002`
- Admin: `http://150.158.121.81:5003`

It runs the `dev` Spring profile with a mock student card. Mock balances reset when the backend container is recreated. Public HTTP is not suitable for real credentials or real payments.

## Maintenance rules

- Applied Flyway migrations are immutable. Add a new numbered migration for schema or data changes.
- Keep credentials in the deployment `.env` or environment variables. Do not place passwords, app secrets, private keys or bearer tokens in source or logs.
- Keep prices and balances in integer cents. Never trust a client-provided price.
- Preserve the idempotent debit/refund contract in `StudentCardClient`.
- Update this directory when commands, endpoints, roles or deployment boundaries change.
- Do not run the destructive smoke-test script against a real shop.
