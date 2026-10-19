# Test deployment

The remote test stack runs the student, barista and admin frontends with the Yudao Java backend, MySQL, Redis and Caddy.

## Compose layout

`deploy/yudao-demo/compose.yaml`:

- Publishes student, barista and admin on ports 5001, 5002 and 5003 by default.
- Keeps MySQL, Redis and the backend on a private Compose network.
- Runs the backend with the `dev` profile, student password login and the in-memory mock student card.
- Drops backend Linux capabilities and runs it as an unprivileged user.

The test frontend currently uses HTTP only. Do not enter real staff, student, DingTalk or payment credentials on this public address.

## Required private `.env`

Create a server-side `.env` with fresh random values:

- `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`
- `REDIS_PASSWORD`
- `OTIA_ADMIN_INITIAL_PASSWORD` (at least 8 characters with both letters and digits)
- `OTIA_DEV_LOGIN_SECRET` (at least 32 random characters)
- `OTIA_STUDENT_INITIAL_NO`, `OTIA_STUDENT_INITIAL_NAME`, `OTIA_STUDENT_INITIAL_PASSWORD`
- `BIND_ADDR`, `STUDENT_PORT`, `BARISTA_PORT`, `ADMIN_PORT`

Keep `.env` mode `600`. Never commit it.

## Release files

```text
deploy/yudao-demo/
  compose.yaml
  caddy/
  mysql-init/
  student/
  barista/
  admin/
  app/yudao-server.jar
  .env
```

Build locally:

```bash
cd apps/backend
export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
mvn -v
mvn clean verify

cd ../frontend/Student
npm run build

cd ../../admin
pnpm run build

cd ../frontend/Barista
npm run build
```

Copy the three `dist/` directories and `apps/backend/yudao-server/target/yudao-server.jar` into the release layout above. Start with:

```bash
sudo docker compose --env-file .env -p otia-cafe-test up -d
```

## Verification

```bash
curl -fsS http://127.0.0.1:5001/healthz
curl -fsS http://127.0.0.1:5002/healthz
curl -fsS http://127.0.0.1:5003/healthz
```

Run the acceptance suite from the repository root against the deployed test stack:

```bash
CAFE_APP_API_URL=http://127.0.0.1:5001 \
CAFE_ADMIN_API_URL=http://127.0.0.1:5003 \
CAFE_ADMIN_PASSWORD='from-private-env' \
CAFE_DEV_LOGIN_SECRET='from-private-env' \
CAFE_MOCK_INITIAL_BALANCE_CENTS=500000 \
python3 scripts/smoke-cafe.py
```

The suite creates temporary employee accounts, changes shop settings temporarily and restores them. It does not submit a card debit outside the dev/mock boundary.

Before considering a production release healthy, verify that passwords shorter than eight characters, letters-only passwords and digits-only passwords are rejected; a URL query token is rejected; a refresh token cannot act as a bearer token; refresh rotation invalidates the previous pair; and an unknown `Origin` receives no `Access-Control-Allow-Origin` header. Request the three frontend pages and confirm the Caddy security headers before opening access.

The latest password-policy release from 2026-10-19 uses JAR SHA-256 `cfb664d47338952c6cc42de9022c3ee45587e67d84298788f4139b5acaa11ff6`. Its complete rollback snapshot is `/home/ubuntu/otia-cafe-demo/stage/release/backup-full-20261019T113753Z`; the previous backend and frontend bundles are also retained beside their current directories with `.previous-20261019T113753Z` suffixes. The release passed all 43 API acceptance checks plus password-policy boundary tests.

## Rollback

Keep timestamped copies of the previous frontend bundle and backend JAR. To roll back, restore those files and recreate only the affected services:

```bash
sudo docker compose --env-file .env -p otia-cafe-test up -d --force-recreate backend student barista admin
```

Database migrations are forward-only. If a migration is wrong, write a corrective migration; do not edit an applied Flyway file.

## Production cutover

1. Provide a trusted domain and TLS certificate. Put the admin and barista routes behind a VPN or an equivalent private access layer; do not publish them directly on `0.0.0.0`.
2. Obtain the school card API contract and test credentials. Implement the client against the same order-number debit/refund idempotency and late-debit barrier used by the mock, then test those races in the school sandbox.
3. Create new production secrets for MySQL, Redis, the initial administrator, DingTalk and any card API. Do not reuse values from the test `.env`.
4. Switch the backend to a production profile and disable `CAFE_AUTH_DEV_LOGIN_ENABLED` and `CAFE_CARD_MOCK_ENABLED`. Startup safety checks intentionally reject that combination under non-dev profiles.
5. Configure encrypted database connections, backup retention, restore drills, log retention, alerting and an on-call path for orders stuck in payment compensation.
6. Build the backend under JDK 21, run all tests and frontend builds, deploy to staging, and run the full smoke suite only against staging. Use read-only and health checks for the production cutover.
7. Keep a timestamped JAR and frontend rollback bundle until the first operating day has completed without unresolved payments.
