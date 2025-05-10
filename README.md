# Food Delivery Microservices Application

A containerized microservices application for a food delivery system, similar to UberEats.

## Services

1. User Service - Handles user authentication and profile management
2. Restaurant Service - Manages restaurant listings and menus
3. Order Service - Handles order placement and tracking
4. Payment Service - Processes payments (mock Stripe API)
5. Delivery Service - Assigns drivers and tracks deliveries

## Technology Stack

- Backend: Flask (Python)
- Databases: PostgreSQL
- Message Broker: AWS SNS/SQS
- Containerization: Docker
- Container Registry: AWS ECR
- Orchestration: AWS ECS
- CI/CD: Jenkins
- Infrastructure as Code: Terraform (coming soon)

## Project Structure

```
microservices-app/
├── docker-compose.yml
├── jenkins/
│   └── Jenkinsfile
├── services/
│   ├── user-service/
│   ├── restaurant-service/
│   ├── order-service/
│   ├── payment-service/
│   └── delivery-service/
├── shared/
│   └── common/
└── README.md
```

## Setup Instructions

1. Clone the repository
2. Set up AWS credentials
3. Create ECR repositories for each service
4. Configure Jenkins pipelines
5. Run services using Docker Compose

## Development

Each service is containerized and can be developed independently. See individual service directories for specific setup instructions.

## License

MIT 