# Order Service

This service handles order management for the food delivery application. It provides endpoints for creating, retrieving, and updating orders.

## Features

- Create new orders with multiple items
- Get order details
- List orders with filtering options
- Update order status
- Integration with User and Restaurant services
- JWT authentication
- Role-based access control

## API Endpoints

### Create Order
```
POST /api/orders
```
Request body:
```json
{
    "restaurant_id": 1,
    "delivery_address": "123 Main St",
    "special_instructions": "Please deliver to the back door",
    "items": [
        {
            "menu_item_id": 1,
            "quantity": 2,
            "special_instructions": "Extra spicy"
        }
    ]
}
```

### Get Orders
```
GET /api/orders
```
Query parameters:
- `status`: Filter by order status
- `restaurant_id`: Filter by restaurant (required for restaurant owners)

### Get Order Details
```
GET /api/orders/<order_id>
```

### Update Order Status
```
PUT /api/orders/<order_id>
```
Request body:
```json
{
    "status": "confirmed"
}
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export FLASK_APP=app
export FLASK_ENV=development
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/order_db
export JWT_SECRET_KEY=your-secret-key
export USER_SERVICE_URL=http://localhost:5000
export RESTAURANT_SERVICE_URL=http://localhost:5000
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
flask run
```

## Running Tests

```bash
pytest
```

## Docker

Build and run with Docker:
```bash
docker build -t order-service .
docker run -p 5000:5000 order-service
```

## Dependencies

- Flask
- SQLAlchemy
- Flask-JWT-Extended
- Marshmallow
- PostgreSQL
- Requests 