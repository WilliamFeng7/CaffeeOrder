# API Documentation

The CoffeeOrder System backend is built with FastAPI. Below is an overview of the main API resources.

> **Note**: For interactive documentation and testing, run the backend and visit `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`.

## Base URL
`http://localhost:8000/api/v1`

## Resources

### 🔐 Authentication (`/auth`)
- **POST /login/access-token**: Login and get JWT access token.
- **POST /login/test-token**: Test current token validity.

### 👥 Users (`/users`)
- Manage user accounts (Students, Baristas, Admins).
- Users can view their own profile; Admins can manage all users.

### ☕ Menu / Products (`/menu`)
- **GET /menu**: List available coffee and products.
- **POST /menu**: Create new product (Admin only).
- **PUT /menu/{id}**: Update product details (Admin only).

### 📝 Orders (`/order`)
- **POST /order**: Place a new order.
- **GET /order**: List orders (filtered by status/user).
- **GET /order/history**: Get current user's order history.
- **PUT /order/{id}/status**: Update order status (Barista/Admin).

### 🛠️ Administration (`/admin`)
- System-wide administrative settings and oversight.

### 💰 Finance (`/finance`)
- **GET /finance/stats**: Retrieve financial statistics and sales data.

### ⚙️ Settings (`/settings`)
- Application configuration and preferences.

## Error Handling

The API uses standard HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Validation Error`: Data validation failed
- `500 Internal Server Error`: Server processing error
