# Frontends

## Applications

| App | Directory | Package manager | State storage |
| --- | --- | --- | --- |
| Student | `apps/frontend/Student` | npm workspace | `sessionStorage` |
| Barista | `apps/frontend/Barista` | npm workspace | `localStorage` |
| Admin | `apps/admin` | pnpm project | local cache and `sessionStorage`-backed stores |

Shared request, API-token and UI primitives are in `packages/shared`. Shared motion tokens are in `packages/shared/styles/motion.css`; shared controls are in `packages/shared/styles/ui.css`.

## Student experience

The student app is optimized for an iPad 10 in Safari or as a home-screen web app.

- Logical viewport: `1180×820` landscape and `820×1180` portrait. Both use the iPad 10 display ratio `59:41`.
- Layout is full-screen with safe-area handling, no page-level horizontal overflow and scroll areas sized around the floating cart and bottom navigation.
- Visible interactive controls use at least a `44×44px` touch target. Adjacent quantity and delete actions keep at least `8px` spacing.
- `prefers-reduced-motion` removes transforms, spring movement and large entrances while preserving short opacity changes.
- Product details, quick cart and checkout support touch and drag dismissal. The cart can be opened from its capsule or bypassed with the adjacent checkout action.
- On iPad portrait, the menu uses a permanent category rail; on smaller phones, categories become a scrollable segmented control.

Before changing the student UI, verify all primary screens and overlays at both iPad logical viewports with `pointer: coarse`, then repeat with reduced motion.

## Barista experience

The barista app uses large order cards and a numeric keypad for the POS receipt number. The board polls the API, can play a notification sound, and keeps its access/refresh tokens only in that device's browser storage. The login page rejects admin accounts that cannot access the barista board.

## Admin experience

The admin app is the retained Yudao management shell.

- At widths up to `900px`, including iPad 10 portrait, navigation moves into a drawer so tables keep usable width.
- Wide tables scroll horizontally rather than crushing Chinese labels and action columns.
- Element Plus buttons, inputs, tabs, menu rows, pagination, dropdowns and form controls are enlarged to touch targets on coarse-pointer devices.
- Admin login warns when the page is served over public HTTP.

## Commands

```bash
# Student
npm run build -w apps/frontend/Student
npx vue-tsc --noEmit -p apps/frontend/Student/tsconfig.json
npm run test:checkout --prefix apps/frontend/Student

# Barista
npm run build -w apps/frontend/Barista

# Admin
pnpm --dir apps/admin build
pnpm --dir apps/admin typecheck
```

## Client-side rules

- Never treat stored role flags or hidden controls as authorization. The backend permission annotation is authoritative.
- Never calculate the final price in the browser. It may only show a preview; the backend recomputes the quote.
- Keep the pending checkout idempotency key until the backend gives a definitive outcome.
- Do not store passwords, DingTalk authorization codes or server secrets in browser storage.
- Use the shared request client so token refresh and unauthorized handling stay consistent.
