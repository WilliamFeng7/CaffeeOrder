# API Documentation

The CoffeeOrder System backend is built with **FastAPI**. This documentation provides a comprehensive guide to the available endpoints, their expected inputs, and returned outputs.

> **Interactive Docs**:
> - **Swagger UI**: `http://localhost:8000/docs` - Interactive testing sandbox.
> - **ReDoc**: `http://localhost:8000/redoc` - Alternative documentation view.

## Base URL
`http://localhost:8000/api/v1`

## Authentication

All protected endpoints require a **JWT Bearer Token** in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

### Role-Based Access Control (RBAC)
| Role | Access Level |
|------|--------------|
| `student` | Own orders, profile, menu browsing |
| `barista` | Order management (KDS), product viewing |
| `admin` | Full access: users, products, finance, settings |

### Rate Limiting & Account Lockout
- **IP-based Rate Limiting**: 10 attempts per minute per device.
- **Progressive Account Lockout**:
  - 5-9 failures: 1 min lockout
  - 10-14 failures: 5 min lockout
  - 15-19 failures: 30 min lockout
  - 20+ failures: 24 hour lockout

---

## Endpoints Reference

### 🔐 Authentication (`/login`)

#### **POST /login/access-token**
OAuth2 compatible login endpoint.

**Request** (Form Data):
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | ✅ | Username, phone, or email |
| `password` | string | ✅ | User password |

**Response** `200 OK`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "role": "student",
  "username": "2023001", 
  "uuid": "u-abc123",
  "name": "张三"
}
```

**Error Responses**:
- `400`: Invalid credentials (`{"code": "failed", "message": "Invalid username or password", "attempts_left": 3}`)
- `403`: Account locked (`{"code": "locked", "message": "Account locked. Try again in 5 minutes.", "wait_minutes": 5}`)

---

### 👥 Users (`/users`)

#### **GET /users/me**
Get current user's profile.

**Response** `200 OK`:
```json
{
  "id": 1,
  "username": "2023001",
  "uuid": "u-abc123",
  "name": "张三",
  "role": "student",
  "balance": 15000,
  "phone": "13800138000",
  "email": "test@example.com"
}
```

#### **PUT /users/me**
Update current user's profile (limited fields).

**Request**:
```json
{
  "name": "李四",
  "phone": "13900000000",
  "email": "new@example.com"
}
```

#### **PUT /users/me/password**
Change password.

**Request**:
```json
{
  "old_password": "currentPass",
  "new_password": "newSecurePass123"
}
```

---

### ☕ Menu (`/menu`)

#### **GET /menu/**
List all active menu items (public).

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "name": "Latte",
    "name_cn": "拿铁",
    "price": 2800,
    "category": "Coffee",
    "image_path": "/static/latte.png",
    "inventory_count": 50,
    "is_recommend": true
  }
]
```

---

### 📝 Orders (`/orders`)

#### **POST /orders/**
Create a new order (Student).

**Request**:
```json
{
  "items": [
    {
      "menu_item_id": 1,
      "spec": {"sugar": "half", "temp": "ice"}
    }
  ]
}
```

**Response** `201 Created`:
```json
{
  "id": 101,
  "order_no": "20261004001",
  "pickup_code": "A001",
  "pickup_number": 1,
  "total_amount": 2800,
  "status": "created",
  "items": [...]
}
```

#### **GET /orders/history**
Get current user's order history.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Items per page |

#### **POST /orders/{order_id}/cancel**
Cancel an order (must be in `created` status).

#### **POST /orders/{order_id}/complete** 
Mark order as completed (Barista/Admin).

#### **GET /orders/sync**
Incremental order sync for KDS (Barista/Admin).

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `since` | float | 0 | Unix timestamp for incremental updates |

#### **PUT /orders/{order_id}/status**
Update order status (Barista/Admin).

**Request**:
```json
{
  "status": "processing"
}
```

**Valid Status Transitions**:
```
created → processing → ready → completed
    ↘ refunded (cancel path)
```

---

### 🛠️ Admin (`/admin`)

> All endpoints require `admin` role.

#### **GET /admin/stats**
Dashboard statistics.

**Response** `200 OK`:
```json
{
  "overview": {
    "total_revenue_today": 560.00,
    "revenue_growth": 12.5,
    "total_orders_today": 25,
    "orders_growth": 8.3,
    "aov_today": 22.40,
    "new_members_today": 3,
    "pending_orders_count": 5
  },
  "operations": {
    "funnel": {
      "pending": 2,
      "processing": 3,
      "ready": 1,
      "completed": 19,
      "cancelled": 0
    },
    "estimated_wait_minutes": 15,
    "trend": [{"hour": "08:00", "orders": 5, "revenue": 112.00}, ...]
  },
  "inventory": {
    "top_selling_items": [{"name": "Latte", "sales": 12}],
    "sold_out_items": [{"name": "燕麦奶", "category": "Add-ons"}]
  }
}
```

#### **GET /admin/users**
List all users.

#### **POST /admin/users**
Create a new user.

**Request**:
```json
{
  "username": "2023002",
  "password": "securePass123",
  "name": "新用户",
  "role": "student",
  "balance": 100.00
}
```

#### **PUT /admin/users/{user_id}**
Update user (can modify role, balance).

#### **DELETE /admin/users/{user_id}**
Delete user (cannot delete admins).

#### **GET /admin/products**
List all products (including inactive).

#### **POST /admin/products**
Create new product.

**Request**:
```json
{
  "name": "Mocha",
  "name_cn": "摩卡",
  "price": 3200,
  "category": "Coffee",
  "inventory_count": 999
}
```

#### **PUT /admin/products/{product_id}**
Update product.

#### **DELETE /admin/products/{product_id}**
Delete product.

#### **GET /admin/orders**
List all orders with optional status filter.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter: `created`, `processing`, `ready`, `completed`, `refunded` |

#### **PUT /admin/orders/{order_id}/status**
Update order status.

---

### 💰 Finance (`/finance`)

> All endpoints require `admin` role.

#### **GET /finance/stats**
Financial overview.

**Response** `200 OK`:
```json
{
  "total_liability": 25000000,
  "today_sales": 56000,
  "today_deposits": 120000,
  "consumption_rate": 100
}
```

#### **GET /finance/chart**
Revenue chart data.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `days` | int | 7 | Time range (1=24h hourly, 7/30=daily) |

**Response** `200 OK`:
```json
{
  "line_chart": [
    {"date": "2026-01-01", "deposit": 500.00, "spending": 320.00}
  ],
  "pie_chart": [
    {"name": "¥50", "value": 15},
    {"name": "¥100", "value": 8}
  ]
}
```

#### **GET /finance/transactions**
Transaction history.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | `order` | `order` or `deposit` |
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Items per page |

---

### ⚙️ Settings (`/settings`)

#### **GET /settings/**
Get all system settings.

#### **PUT /settings/{key}**
Update a setting (Admin only).

**Request**:
```json
{
  "value": "new_value"
}
```

---

## Error Response Format

All errors follow a consistent format:

```json
{
  "detail": "Error message here"
}
```

Or for validation errors (`422`):
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

## Status Codes Summary

| Code | Meaning | Common Cause |
|------|---------|--------------|
| `200` | OK | Successful GET/PUT |
| `201` | Created | Successful POST |
| `400` | Bad Request | Invalid credentials, duplicate username |
| `401` | Unauthorized | Missing/expired token |
| `403` | Forbidden | Insufficient role privileges, account locked |
| `404` | Not Found | Resource ID doesn't exist |
| `422` | Validation Error | Invalid data types/formats |
| `500` | Server Error | Unexpected backend exception |
