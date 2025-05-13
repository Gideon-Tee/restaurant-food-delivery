# Food Delivery App API Documentation

## Base URLs
- User Service: `http://localhost:5001/api`
- Restaurant Service: `http://localhost:5002/api`
- Order Service: `http://localhost:5003/api`

## Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## User Service API

### Register a New User
```http
POST /users/register
```

**Request Body:**
```json
{
    "username": "string",
    "email": "string",
    "password": "string"
}
```

**Response (201 Created):**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
}
```

### User Login
```http
POST /users/login
```

**Request Body:**
```json
{
    "email": "string",
    "password": "string"
}
```

**Response (200 OK):**
```json
{
    "access_token": "string",
    "user": {
        "id": "integer",
        "username": "string",
        "email": "string"
    }
}
```

### Get User Profile
```http
GET /users/profile
```

**Headers:**
- Authorization: Bearer token required

**Response (200 OK):**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
}
```

## Restaurant Service API

### Create Restaurant
```http
POST /restaurants
```

**Headers:**
- Authorization: Bearer token required
- Content-Type: application/json

**Request Body:**
```json
{
    "name": "string",
    "description": "string",
    "address": "string",
    "phone_number": "string",
    "email": "string",
    "cuisine_type": "string",
    "opening_hours": "string (JSON)",
    "is_active": "boolean"
}
```

**Response (201 Created):**
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "address": "string",
    "phone_number": "string",
    "email": "string",
    "cuisine_type": "string",
    "opening_hours": "string (JSON)",
    "is_active": "boolean",
    "owner_id": "integer",
    "created_at": "datetime"
}
```

### Get All Restaurants
```http
GET /restaurants
```

**Query Parameters:**
- `cuisine_type` (optional): Filter by cuisine type
- `is_active` (optional): Filter by active status (true/false)

**Response (200 OK):**
```json
[
    {
        "id": "integer",
        "name": "string",
        "description": "string",
        "address": "string",
        "phone_number": "string",
        "email": "string",
        "cuisine_type": "string",
        "opening_hours": "string (JSON)",
        "is_active": "boolean",
        "owner_id": "integer",
        "created_at": "datetime"
    }
]
```

### Get Restaurant by ID
```http
GET /restaurants/{restaurant_id}
```

**Response (200 OK):**
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "address": "string",
    "phone_number": "string",
    "email": "string",
    "cuisine_type": "string",
    "opening_hours": "string (JSON)",
    "is_active": "boolean",
    "owner_id": "integer",
    "created_at": "datetime"
}
```

### Update Restaurant
```http
PUT /restaurants/{restaurant_id}
```

**Headers:**
- Authorization: Bearer token required
- Content-Type: application/json

**Request Body:**
```json
{
    "name": "string (optional)",
    "description": "string (optional)",
    "address": "string (optional)",
    "phone_number": "string (optional)",
    "email": "string (optional)",
    "cuisine_type": "string (optional)",
    "opening_hours": "string (JSON) (optional)",
    "is_active": "boolean (optional)"
}
```

**Response (200 OK):**
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "address": "string",
    "phone_number": "string",
    "email": "string",
    "cuisine_type": "string",
    "opening_hours": "string (JSON)",
    "is_active": "boolean",
    "owner_id": "integer",
    "created_at": "datetime"
}
```

### Create Menu Item
```http
POST /restaurants/{restaurant_id}/menu
```

**Headers:**
- Authorization: Bearer token required
- Content-Type: application/json

**Request Body:**
```json
{
    "name": "string",
    "description": "string",
    "price": "float",
    "category": "string",
    "is_available": "boolean"
}
```

**Response (201 Created):**
```json
{
    "id": "integer",
    "restaurant_id": "integer",
    "name": "string",
    "description": "string",
    "price": "float",
    "category": "string",
    "is_available": "boolean",
    "created_at": "datetime"
}
```

### Get Restaurant Menu Items
```http
GET /restaurants/{restaurant_id}/menu
```

**Query Parameters:**
- `category` (optional): Filter menu items by category

**Response (200 OK):**
```json
[
    {
        "id": "integer",
        "restaurant_id": "integer",
        "name": "string",
        "description": "string",
        "price": "float",
        "category": "string",
        "is_available": "boolean",
        "created_at": "datetime"
    }
]
```

## Error Responses

### Validation Error (422 Unprocessable Entity)
```json
{
    "error": "Validation error",
    "details": {
        "field_name": ["error message"]
    }
}
```

### Authentication Error (401 Unauthorized)
```json
{
    "error": "Missing Authorization Header"
}
```

### Authorization Error (403 Forbidden)
```json
{
    "error": "Unauthorized"
}
```

### Not Found Error (404 Not Found)
```json
{
    "error": "Resource not found"
}
```

### Server Error (500 Internal Server Error)
```json
{
    "error": "Internal server error",
    "details": "Error message"
}
```

## Example Usage

### 1. Register a new user
```bash
curl -X POST http://localhost:5001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. Login to get JWT token
```bash
curl -X POST http://localhost:5001/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 3. Create a restaurant (using the JWT token)
```bash
curl -X POST http://localhost:5002/api/restaurants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Test Restaurant",
    "description": "A test restaurant",
    "address": "123 Test St",
    "phone_number": "1234567890",
    "email": "restaurant@example.com",
    "cuisine_type": "Italian",
    "opening_hours": "{\"monday\": \"09:00-22:00\"}",
    "is_active": true
  }'
```

### 4. Add a menu item
```bash
curl -X POST http://localhost:5002/api/restaurants/1/menu \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Margherita Pizza",
    "description": "Classic tomato and mozzarella pizza",
    "price": 12.99,
    "category": "Pizza",
    "is_available": true
  }'
```

## Order Service API

### Create Order
```http
POST /orders
```

**Headers:**
- Authorization: Bearer token required
- Content-Type: application/json; charset=utf-8

**Request Body:**
```json
{
    "restaurant_id": 1,
    "delivery_address": "123 Main St",
    "special_instructions": "Optional delivery instructions",
    "items": [
        {
            "menu_item_id": 1,
            "quantity": 2,
            "special_instructions": "Extra spicy"
        },
        {
            "menu_item_id": 2,
            "quantity": 1
        }
    ]
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "customer_id": "1",
    "restaurant_id": 1,
    "status": "pending",
    "total_amount": 25.98,
    "delivery_address": "123 Main St",
    "special_instructions": "Optional delivery instructions",
    "items": [
        {
            "id": 1,
            "menu_item_id": 1,
            "quantity": 2,
            "price_at_time": 9.99,
            "special_instructions": "Extra spicy"
        },
        {
            "id": 2,
            "menu_item_id": 2,
            "quantity": 1,
            "price_at_time": 6.00,
            "special_instructions": null
        }
    ],
    "created_at": "2024-03-14T12:00:00Z",
    "updated_at": "2024-03-14T12:00:00Z"
}
```

### Get All Orders
```http
GET /orders
```

**Headers:**
- Authorization: Bearer token required

**Query Parameters:**
- `status` (optional): Filter by order status (pending, confirmed, preparing, ready, delivered, cancelled)
- `restaurant_id` (optional): Required for restaurant owners to filter orders

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "customer_id": "1",
        "restaurant_id": 1,
        "status": "pending",
        "total_amount": 25.98,
        "delivery_address": "123 Main St",
        "special_instructions": "Optional delivery instructions",
        "items": [
            {
                "id": 1,
                "menu_item_id": 1,
                "quantity": 2,
                "price_at_time": 9.99,
                "special_instructions": "Extra spicy"
            }
        ],
        "created_at": "2024-03-14T12:00:00Z",
        "updated_at": "2024-03-14T12:00:00Z"
    }
]
```

### Get Single Order
```http
GET /orders/{order_id}
```

**Headers:**
- Authorization: Bearer token required

**Response (200 OK):**
```json
{
    "id": 1,
    "customer_id": "1",
    "restaurant_id": 1,
    "status": "pending",
    "total_amount": 25.98,
    "delivery_address": "123 Main St",
    "special_instructions": "Optional delivery instructions",
    "items": [
        {
            "id": 1,
            "menu_item_id": 1,
            "quantity": 2,
            "price_at_time": 9.99,
            "special_instructions": "Extra spicy"
        }
    ],
    "created_at": "2024-03-14T12:00:00Z",
    "updated_at": "2024-03-14T12:00:00Z"
}
```

### Update Order Status
```http
PUT /orders/{order_id}
```

**Headers:**
- Authorization: Bearer token required
- Content-Type: application/json; charset=utf-8

**Request Body:**
```json
{
    "status": "confirmed"
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "customer_id": "1",
    "restaurant_id": 1,
    "status": "confirmed",
    "total_amount": 25.98,
    "delivery_address": "123 Main St",
    "special_instructions": "Optional delivery instructions",
    "items": [
        {
            "id": 1,
            "menu_item_id": 1,
            "quantity": 2,
            "price_at_time": 9.99,
            "special_instructions": "Extra spicy"
        }
    ],
    "created_at": "2024-03-14T12:00:00Z",
    "updated_at": "2024-03-14T12:00:00Z"
}
```

## Example Usage

### Create an Order
```bash
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "restaurant_id": 1,
    "delivery_address": "123 Main St",
    "special_instructions": "Please deliver to the back door",
    "items": [
      {
        "menu_item_id": 1,
        "quantity": 2,
        "special_instructions": "Extra spicy"
      },
      {
        "menu_item_id": 2,
        "quantity": 1
      }
    ]
  }'
```

### Get All Orders
```bash
curl -X GET http://localhost:5003/api/orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Single Order
```bash
curl -X GET http://localhost:5003/api/orders/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Order Status
```bash
curl -X PUT http://localhost:5003/api/orders/1 \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "status": "confirmed"
  }'
```

## Service Integration
The services communicate with each other:
- User Service: Handles authentication and user management
- Restaurant Service: Manages restaurants and menu items
- Order Service: Processes orders and integrates with both User and Restaurant services 