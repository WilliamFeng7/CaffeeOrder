# Tech Debt Analysis for Frontend Student App

This document catalogs technical debt identified in the `frontend/Student` application. Use this as a guide for future refactoring.

## 1. API Layer (`src/api/index.ts`)

### A. Major Performance & Logic Issues
- **Inefficient Order Creation Logic**: The `createOrder` function currently expands items based on quantity before sending them to the backend:
  ```typescript
  for (let i = 0; i < item.quantity; i++) {
      backendItems.push({ ... });
  }
  ```
  This results in large payloads and unnecessary processing. The backend `OrderItemSchema` supports a `quantity` field.
  **Action**: Refactor `createOrder` to send a single object per unique item with a `quantity` property.

### B. Type Safety Violations
- **Widespread `any` Usage**:
  - `login` returns `Promise<any>`.
  - `getMenu` maps over `item: any`.
  - `getMyOrders` iterates `o.items` as `any`.
  - `updatePassword` catches `error: any`.
  **Action**: Define strict interfaces for all API responses and request payloads. Use Zod for runtime validation if possible.

- **Manual Type Mapping**: The mapping logic in `getMenu` and `getMyOrders` is manual, verbose, and error-prone.
  **Action**: Use a shared types library or auto-generated clients (e.g., via OpenAPI/Swagger codegen) to ensure frontend types match backend Pydantic models.

### C. Error Handling
- **Swallowed Errors**: `getMenu` and `getMyOrders` catch errors and simply return empty arrays (`[]`).
  ```typescript
  catch (error) {
      console.error('Failed to fetch menu:', error);
      return [];
  }
  ```
  This hides critical failures (e.g., network down, server error 500) from the user, making the app appear empty rather than broken.
  **Action**: Implement proper error propagation or a global error handler to show UI feedback (toast/alert) to the user.

- **Fragile Error Parsing**: `updatePassword` manually parses error strings.
  **Action**: Standardize backend error responses and use a consistent helper to extract messages.

### D. Magic Numbers & Strings
- **Currency Conversion**: `price / 100` and `total_amount / 100` appear repeatedly.
  **Action**: Create a `Money` value object or utility functions `centsToYuan(cents: number)` and `yuanToCents(yuan: number)` to centralize this logic.
- **Hardcoded Strings**: Strings like `'Regular'`, `'Hot'` are hardcoded.
  **Action**: Use enums or constants for product specifications.

## 2. General Code Quality
- **Missing Linting (Fixed)**: ESLint and Prettier were missing. They have now been installed.
- **Component Decomposition**: `MenuHeader.vue` and `ProductGrid.vue` (mentioned in system memory) should be reviewed for size and complexity.

## 3. Recommendations
1. **Prioritize the Order Creation Fix**: This directly impacts network performance and backend load.
2. **Strict Mode**: Enable `noImplicitAny` in `tsconfig.json` after fixing the API layer.
