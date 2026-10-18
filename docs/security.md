# Security guide

## Implemented controls

- Student passwords use BCrypt and require 12–72 bytes during bootstrap. Staff password creation/reset requires 12–16 characters.
- Student and staff login attempts are throttled by account and source IP in Redis.
- Access and refresh tokens use separate user types and API prefixes. Refresh tokens are atomically consumed and rotated once, and are never accepted as bearer access tokens.
- Administrator refresh locks the user row and re-reads the refresh token, so password changes and token renewal cannot race. Session revocation deletes refresh rows by user, including orphaned refresh records.
- Bearer tokens are accepted only from `Authorization`, not from URL query parameters.
- CORS is same-origin by default. Cross-origin use requires an explicit `yudao.web.cors.allowed-origins` allowlist; wildcard credentialed CORS is not enabled.
- The development student login requires `X-Cafe-Dev-Secret`, configured as `OTIA_DEV_LOGIN_SECRET` with at least 32 random characters.
- The generic framework mock-login secret has no public default and remains unusable unless a secret is explicitly configured.
- Initial admin startup requires `OTIA_ADMIN_INITIAL_PASSWORD`. Flyway `V6` clears the legacy public bootstrap password before the operator-supplied password is applied.
- System-initiated operation logs use the reserved audit identity `user_id=0` and nonempty internal request fields. Bootstrap password changes therefore produce a durable audit row instead of failing the operation-log insert.
- Request, login and operation logs redact passwords, tokens, authorization codes, secrets and OTPs. Password reset operation logs retain the event but not password hashes.
- The remote Caddy edge sets CSP, frame restrictions, MIME sniffing protection, referrer policy, cross-origin resource policy and restrictive browser permissions.
- Upload and presigned-upload endpoints require `infra:file:upload`; file content is sniffed, path traversal is rejected and only bitmap image types are accepted.
- Staff directory lists, nickname search, avatar cards and user-import templates require `system:user:query` or `system:user:import`; barista accounts cannot enumerate staff accounts.
- The Compose backend runs as an unprivileged UID with all Linux capabilities dropped and `no-new-privileges`.
- Tomcat is pinned to `10.1.61`, replacing the Spring Boot-managed `10.1.55` after reviewing the August 2026 critical DIGEST, authorization and FORM-authentication advisories.
- Jackson `2.21.7`, Netty `4.1.137.Final`, Log4j API `2.25.5`, commons-lang3 `3.20.0` and dynamic-datasource `4.6.0` replace dependency versions with published advisories.

## Financial controls

- Server-side pricing and option validation.
- Per-student draft lock and scoped idempotency keys.
- Debit after local commit; compensation for unknown outcomes; scheduled refund retries.
- Status/version compare-and-set transitions and unique POS receipt numbers per business date.
- Snapshotting of historical order lines.

Run the backend security and money tests after any change to these controls:

```bash
cd apps/backend
export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
mvn -v                         # 应为 Java 21
mvn clean verify
```

Then run `scripts/smoke-cafe.py` only against the dev/mock test stack.

## Verification completed on 2026-10-18

- Backend: all 16 Maven modules passed `clean verify` under JDK 21.
- Deployed API: all 43 `scripts/smoke-cafe.py` checks passed against the remote test stack, including server-side pricing, 5,000 yuan mock balance, idempotent debit, order transitions, queue counts, reporting, export, role separation and session revocation.
- Authentication: legacy `admin123`, URL query tokens, refresh tokens used as bearer tokens and replayed refresh tokens were rejected; refresh rotation and password-change revocation were verified.
- Concurrency: the refresh token is consumed by an atomic database delete; losing concurrent refreshes cannot mint a second token pair. Password change and refresh serialization use the administrator user row lock.
- Edge and initialization: unknown CORS origins were rejected; CSP, frame, MIME, referrer, CORP and browser-permission headers were present; empty bootstrap admin state recovered from the private password and wrote a system audit row.
- Logging: the remote log scan found zero bearer/refresh-token/password values and zero startup data-integrity failures after the final deployment.
- Dependencies: npm and pnpm production audits reported zero known vulnerabilities. OSV found no reachable advisory in the final Maven runtime set; Spring MVC `6.2.19` retains upstream advisories for unused XSLT views and SSE view fragments, so it must be upgraded when a patched Spring Boot-supported release is available.

## Required before production

1. Put all three frontends behind a trusted TLS certificate. Public HTTP must not receive real staff or student credentials.
2. Restrict the admin and barista ingress to a VPN or equivalent private access layer.
3. Provide the school's real student-card API documentation and test credentials.
4. Implement `StudentCardClient` with the same order-number idempotency and refund-barrier semantics as the contract.
5. Rotate every test password, token, DingTalk secret and database credential before cutover.
6. Configure encrypted database connections, backups, log retention, alerting and a tested restore process.
7. Disable or secret-protect development login outside the test deployment.

The mock card is in-memory test data and must never be treated as a real balance authority.

The current Codex Security result is [security-review-2026-10-18.md](security-review-2026-10-18.md). It records one remaining medium transport finding; the five issues from the earlier snapshot are fixed and regression-tested.

## Current known deployment limitation

The published remote test stack still listens on cleartext HTTP. Login throttling, input validation and on-page warnings do not replace transport encryption. The current student-card implementation is a mock, so this environment cannot certify real-money behavior.
