# Security review: 2026-10-18

This page summarizes the current Codex Security result. The full generated report and SARIF export remain in the local security scan workspace and are intentionally excluded from source control.

The scan covered the Java backend, three frontend projects, shared client code, startup scripts, Flyway migrations and deployment configuration. Generated `target`, `dist` and `node_modules` trees were excluded from line-by-line review; production dependency audits were run separately. Coverage is partial because the real school student-card provider contract is unavailable.

## Current result

One medium deployment finding remains:

| Severity | CWE | Finding | Required action |
| --- | --- | --- | --- |
| Medium | CWE-319 | Student and staff credentials cross public cleartext HTTP | Enable trusted TLS, redirect HTTP to HTTPS, and place the barista and admin consoles behind a VPN or identity-aware proxy |

The current test stack publishes Caddy HTTP port 80 as `150.158.121.81:5001`, `:5002` and `:5003`. Passwords and reusable bearer tokens are therefore visible to a network-path attacker. Security headers, login throttling and session revocation reduce adjacent risk but cannot provide transport confidentiality. Do not use this public address with real credentials or payments.

## Fixed findings from the earlier scan

The initial security review reported five issues. They were fixed and regression-tested:

| Original severity | Finding | Current control |
| --- | --- | --- |
| High | Public fixed administrator password | Flyway `V6` clears the old hash and startup requires an explicitly configured administrator password. All staff passwords now require at least eight characters with both letters and digits |
| Medium | Alternate upload routes lacked permission checks | Backend upload, presigned upload and direct-upload registration all require `infra:file:upload` |
| Medium | Password changes did not revoke sessions | Both password-change paths delete access tokens and refresh tokens in the same transaction |
| Medium | Admin login had no brute-force throttling | Atomic Redis limits cover account and source IP dimensions |
| Low | Initialization audit logging could fail | System actions use the reserved `user_id=0` audit identity and nonempty request fields |

Additional hardening in the final build:

- Refresh tokens are consumed with an atomic database delete. Concurrent refreshes can create only one new pair.
- Administrator refresh takes the user row lock before re-reading and consuming the token, so password changes and token issuance cannot interleave.
- Session revocation deletes refresh tokens by user directly, including refresh records whose access token rows were already cleaned up.
- Tomcat is pinned to `10.1.61` after reviewing the August 2026 critical advisories affecting the Spring Boot-managed `10.1.55`.
- Jackson is pinned to `2.21.7`, Netty to `4.1.137.Final`, Log4j API to `2.25.5`, and dynamic-datasource to `4.6.0`; all four replacements remove the applicable OSV advisories while retaining Spring Boot 3.5 compatibility.
- Maven runtime coordinates were checked against OSV. The only advisory-bound coordinate left is Spring Framework Web MVC `6.2.19`. Its XSLT-view RCE test requires an XSLT view resolver and catch-all view-returning mapping, and its SSE-fragment test requires SSE view fragments; neither feature exists in this application. No patched Spring Framework `6.2.x` release was available when this review was completed, so the application remains on the Spring Boot-supported version and must upgrade when the upstream backport ships.
- The mock authentication secret has no public default; without an explicit secret, mock login remains disabled.
- Bearer tokens are accepted only from `Authorization`, not from URL query parameters.
- CORS is same-origin by default with no wildcard or credentialed cross-origin access.
- Upload content is sniffed as JPEG, PNG, WebP or GIF, and storage paths reject traversal.
- Caddy adds CSP, frame restrictions, MIME protection, CORP, Referrer-Policy and Permissions-Policy.

## Verification

- JDK 21 `mvn clean verify`: all 16 backend modules passed.
- Remote acceptance: all 43 `scripts/smoke-cafe.py` checks passed against the deployed test stack.
- Frontend: Student and Barista production builds passed; Student checkout tests passed 5/5; Student and admin type checks passed.
- Authentication: password login, the shared eight-character letter-and-digit policy, query-token rejection, refresh-token bearer rejection, one-time refresh rotation, old-refresh rejection and password-change session revocation passed.
- Edge: unknown CORS origins received no allow header; all three frontends returned the required security headers and successful static assets.
- Logs: backend logs contained no configured passwords/secrets, bearer tokens, access tokens or refresh tokens.
- Migrations: Flyway versions 1–6 are successful; the administrator password is a nonempty BCrypt hash and not the legacy `$2a$04$` value.
- Dependencies: production npm and pnpm audits reported zero known vulnerabilities. OSV reported no reachable advisory after the Tomcat, Jackson, Netty, Log4j, commons-lang3 and dynamic-datasource upgrades; the remaining Spring MVC advisory is limited to unused XSLT and SSE view features.

## Production blockers

1. Configure a trusted domain and TLS for all browser and API traffic.
2. Restrict barista and admin ingress to a VPN or identity-aware private proxy.
3. Integrate the real school student-card provider and verify debit/refund idempotency and the late-debit barrier in its test environment.
4. Switch to a production profile and disable development login and the mock card.
5. Rotate all test passwords, token-signing material, DingTalk secrets, MySQL credentials and Redis credentials.
6. Add encrypted database connections, tested backups and restores, log retention, payment-compensation alerts and an on-call procedure.
