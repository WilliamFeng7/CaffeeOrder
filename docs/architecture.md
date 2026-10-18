# Architecture

OTIA Café is a three-frontend ordering system backed by one Spring Boot service. The backend is a trimmed Yudao Java monolith using MySQL and Redis.

## Runtime map

| Component | Directory | Authentication | Main responsibility |
| --- | --- | --- | --- |
| Student app | `apps/frontend/Student` | DingTalk or student number/password | Menu, cart, card payment, pickup status |
| Barista app | `apps/frontend/Barista` | Staff account with barista permissions | Enter orders into the shop POS and update preparation state |
| Admin app | `apps/admin` | Staff account with admin/manager permissions | Menu, shop settings, orders, users and roles |
| API | `apps/backend/yudao-server` | OAuth2 bearer tokens | Shared business and administration service |
| Cafe module | `apps/backend/yudao-module-cafe` | Uses shared security | Menu, students, orders, payments, queue and reports |

The browser always calls the API through the same-origin Caddy route (`/app-api` or `/admin-api`). Access tokens are sent in `Authorization: Bearer ...`; tokens in URL query parameters are disabled.

## Authentication and authorization

- Student password login checks a BCrypt hash, returns a generic credential error and applies account/source-IP rate limits.
- DingTalk login exchanges the authorization code and app credentials on the server.
- Student OAuth tokens use `MEMBER`; staff tokens use `ADMIN`. The security filter rejects a token used against the wrong API prefix.
- Admin and barista methods require explicit `@PreAuthorize` permissions. A barista account has no admin menu and cannot manage the menu, users or alternate upload endpoints.
- Password changes revoke the account's existing access and refresh tokens.
- Refresh tokens are single-use and rotated. They cannot be used as bearer access tokens.
- Login, request and operation logs redact passwords, authorization codes, access tokens, refresh tokens and client secrets.

## Order and money invariants

1. The authenticated student identity comes from the token; the browser never supplies `studentId`.
2. Menu availability, selected option groups, cup count and every price are recomputed from current server data.
3. The order total is an integer amount in cents. Client prices are ignored.
4. The local draft is committed before the student-card debit. The student row is locked during draft creation.
5. `Idempotency-Key` is scoped to one student. Repeating the same key and payload returns the original order; changing the payload is rejected.
6. An unresolved debit blocks another charge for that student. Timed-out attempts enter compensation and retry refunds.
7. Card debit and refund use the App order number as the external idempotency key. A confirmed refund also blocks a late debit for that order number.
8. Order state transitions use status plus optimistic version checks. Duplicate taps cannot move an order through a transition twice.
9. Student and barista APIs never expose internal payment states. Admin reports show order count, total amount and confirmed paid amount separately.
10. Product name, image, unit price, options and quantity are stored as order snapshots, so later menu edits do not change history.

## Order state model

| Internal/external value | Meaning |
| --- | --- |
| `0` | Payment in progress; admin only |
| `1` | Payment failed or compensated; admin only |
| `2` | Payment in progress while compensation is retried; admin only |
| `10` | Paid, waiting for barista entry |
| `20` | POS receipt number entered, preparing |
| `30` | Preparation complete |

Only states `10`, `20` and `30` are returned to student and barista clients.

## API map

All responses use `{ code, data, msg }`. Paths below omit the `/app-api` or `/admin-api` prefix.

### Student

| Method and path | Purpose |
| --- | --- |
| `GET /cafe/auth/dingtalk-config` | Public DingTalk config and password-login flag |
| `POST /cafe/auth/dingtalk-login` | Exchange a DingTalk authorization code |
| `POST /cafe/auth/password-login` | Student number and password login |
| `POST /cafe/auth/dev-login` | Dev-only mock login; requires `X-Cafe-Dev-Secret` |
| `GET /cafe/student/me` | Student profile and card balance |
| `GET /cafe/menu` | Public enabled menu |
| `GET /cafe/shop/status` | Public open state, banner and business hours |
| `POST /cafe/order/create` | Create and charge an order |
| `GET /cafe/order/page` | Current student's visible orders |
| `GET /cafe/order/queue` | Today's waiting and preparing count |

### Barista

| Method and path | Permission |
| --- | --- |
| `GET /cafe/barista/order/board` | `cafe:barista:query` |
| `PUT /cafe/barista/order/enter` | `cafe:barista:update` |
| `PUT /cafe/barista/order/done` | `cafe:barista:update` |
| `PUT /cafe/barista/order/undo-done` | `cafe:barista:update` |

### Admin

The admin UI uses the retained Yudao identity, role and permission endpoints under `/system`, plus:

- `/cafe/menu-item`, `/cafe/category`, `/cafe/option-group`, `/cafe/shop`
- `/cafe/order/page`, `/cafe/order/get`, `/cafe/order/statistics`, `/cafe/order/export-excel`
- `/infra/file/upload` for menu images

## Data and deployment

- MySQL stores identities, menu, orders, snapshots, permissions and audit data.
- Redis caches OAuth tokens and login throttling counters.
- Flyway migrations live in `apps/backend/sql/mysql/`. `V1` through `V3` create the trimmed base, cafe schema and security data cleanup; `V4` adds student passwords; `V5` scrubs old sensitive operation logs; `V6` invalidates the legacy default admin password.
- The remote test stack publishes only the three Caddy frontends. MySQL, Redis and the backend stay on the private Compose network.
- The real student-card adapter is not implemented. See [security.md](security.md) and `StudentCardClient` before using real money.
