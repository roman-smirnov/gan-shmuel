# Billing Microservice

Billing system for Gan Shmuel juice factory that calculates payments to fruit providers based on delivery weights and rates.

## Overview

The Billing service tracks fruit providers, their trucks, product rates, and generates billing reports by integrating with the Weight service to retrieve delivery data.

---

## Features

- **Provider Management**: Register and update fruit providers
- **Truck Registration**: Link trucks to providers
- **Rate Management**: Upload and manage product pricing (global and provider-specific)
- **Bill Generation**: Calculate payments based on deliveries and rates
- **Weight Service Integration**: Retrieve weighing data from Weight microservice

---

## Tech Stack

- **Language**: Python 3.12
- **Framework**: Flask
- **Database**: MySQL 8.0
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest with pytest-mock

---

## Project Structure
```
billing/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration
│   ├── routes/
│   │   ├── health.py            # Health check endpoint
│   │   ├── providers.py         # Provider endpoints
│   │   ├── trucks.py            # Truck endpoints
│   │   ├── rates.py             # Rates endpoints
│   │   └── bills.py             # Billing calculation endpoint
│   ├── models/
│   │   ├── provider.py          # Provider DB operations
│   │   ├── truck.py             # Truck DB operations
│   │   └── rate.py              # Rate DB operations
│   ├── services/
│   │   ├── billing_service.py   # Bill calculation logic
│   │   ├── weight_client.py     # Weight service API client
│   │   └── rate_parser.py       # Excel rate file parser
│   └── utils/
│       └── __init__.py          # DB connection utilities
├── tests/
│   ├── test_health.py
│   ├── test_providers.py
│   ├── test_trucks.py
│   ├── test_rates.py
│   └── test_bills.py
├── db/
│   ├── Dockerfile               # MySQL Dockerfile
│   └── billingdb.sql            # Database schema
├── in/                          # Rate file uploads folder
│   └── rates.xlsx               # Sample rates file
├── Dockerfile                   # Flask app Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py                       # Application entry point
└── README.md
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Port 8083 available (or configure `BILLING_PORT` in `.env`)

### 1. Build and Start
```bash
# Build and start all services
docker compose up --build -d

# Check services are running
docker compose ps
```

### 2. Verify Health
```bash
curl http://localhost:8083/health
# Expected: OK
```

### 3. Access Database (Optional)
```bash
docker compose exec billing-db mysql -u root -ppassword billdb
```

---

## API Endpoints

### Health Check
```bash
GET /health
```
Returns `OK` if service and database are healthy.

---

### Provider Management

#### Create Provider
```bash
POST /provider
Content-Type: application/json

{
  "name": "Fresh Farms"
}

# Response: {"id": 10001}
```

#### Update Provider
```bash
PUT /provider/{id}
Content-Type: application/json

{
  "name": "Updated Name"
}

# Response: {"id": 10001, "name": "Updated Name"}
```

---

### Truck Management

#### Register Truck
```bash
POST /truck
Content-Type: application/json

{
  "id": "T-14409",
  "provider": 10001
}
```

#### Update Truck's Provider
```bash
PUT /truck/{id}
Content-Type: application/json

{
  "provider": 10002
}
```

#### Get Truck Info
```bash
GET /truck/{id}?from=yyyymmddhhmmss&to=yyyymmddhhmmss

# Response:
{
  "id": "T-14409",
  "tara": 5000,
  "sessions": [1001, 1002, 1003]
}
```

---

### Rate Management

#### Upload Rates
```bash
POST /rates
Content-Type: application/json

{
  "file": "rates.xlsx"
}
```

Place Excel file in `./in/` folder with format:

| Product | Rate | Scope |
|---------|------|-------|
| Navel | 93 | All |
| Mandarin | 104 | All |
| Mandarin | 120 | 10001 |

- **Scope**: `All` for global rate, or provider ID for provider-specific rate
- Provider-specific rates override global rates

#### Get All Rates
```bash
GET /rates

# Response: Array of rate objects
```

---

### Billing

#### Generate Bill
```bash
GET /bill/{provider_id}?from=yyyymmddhhmmss&to=yyyymmddhhmmss

# Defaults:
# - from: 1st of current month at 000000
# - to: current datetime

# Response:
{
  "id": "10001",
  "name": "Fresh Farms",
  "from": "20241101000000",
  "to": "20241130235959",
  "truckCount": 2,
  "sessionCount": 5,
  "products": [
    {
      "product": "Navel",
      "count": "3",
      "amount": 17700,
      "rate": 93,
      "pay": 1646100
    },
    {
      "product": "Mandarin",
      "count": "2",
      "amount": 15600,
      "rate": 104,
      "pay": 1622400
    }
  ],
  "total": 3268500
}
```

**Note**: Billing integrates with Weight service to retrieve delivery data.

---

## Environment Variables

Create `.env` file in billing directory:
```bash
# Flask Configuration
FLASK_ENV=development

# Database Configuration
DB_HOST=billing-db
DB_USER=root
DB_PASSWORD=password
DB_NAME=billdb
DB_PORT=3306

# External Services
WEIGHT_BASE_URL=http://weight-app:5000

# MySQL Root Configuration
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=billdb

# Port Configuration
BILLING_PORT=8083
```

---

## Development

### Run Tests
```bash
# Run all tests
docker compose exec billing-app pytest tests/ -v

# Run specific test file
docker compose exec billing-app pytest tests/test_bills.py -v

# Run with coverage
docker compose exec billing-app pytest tests/ --cov=app -v
```

### View Logs
```bash
# Follow logs
docker compose logs -f billing-app

# View recent logs
docker compose logs --tail=100 billing-app
```

### Access Container Shell
```bash
docker compose exec billing-app sh
```

### Restart Services
```bash
# Restart billing app only
docker compose restart billing-app

# Restart all services
docker compose restart
```

---

## Database Schema

### Provider
```sql
CREATE TABLE Provider (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255)
) AUTO_INCREMENT=10001;
```

### Trucks
```sql
CREATE TABLE Trucks (
  id VARCHAR(10) PRIMARY KEY,
  provider_id INT,
  FOREIGN KEY (provider_id) REFERENCES Provider(id)
);
```

### Rates
```sql
CREATE TABLE Rates (
  product_id VARCHAR(50) NOT NULL,
  rate INT DEFAULT 0,
  scope VARCHAR(50) DEFAULT NULL
);
```

**Rate Lookup Logic:**
1. Check for provider-specific rate (`scope = provider_id`)
2. If not found, use global rate (`scope = 'All'`)
3. If neither exists, rate = 0

---

## Integration with Weight Service

The Billing service calls the Weight service for:

1. **GET /weight** - Retrieve all weighing sessions in date range
2. **GET /session/{id}** - Get truck information for each session

**Expected Weight Service URL**: `http://weight-app:5000` (configurable via `WEIGHT_BASE_URL`)

---

## Docker Commands
```bash
# Build and start
docker compose up --build -d

# Start (without rebuild)
docker compose up -d

# Stop services
docker compose down

# Stop and remove volumes (clears database)
docker compose down -v

# View running containers
docker compose ps

# Access database
docker compose exec billing-db mysql -u root -ppassword billdb

# Run tests
docker compose exec billing-app pytest tests/

# View logs
docker compose logs -f billing-app
```

---

## Troubleshooting

### Port Already in Use
```bash
# Change BILLING_PORT in .env
BILLING_PORT=8084

# Rebuild
docker compose up --build -d
```

### Database Connection Failed
```bash
# Check database is healthy
docker compose ps

# Wait for database initialization (30 seconds)
# Then restart app
docker compose restart billing-app
```

### Weight Service Unavailable
```bash
# Verify Weight service is running
curl http://localhost:8082/health

# Check network connectivity from billing container
docker compose exec billing-app ping weight-app
```

### Tests Failing
```bash
# Rebuild and run tests
docker compose down -v
docker compose up --build -d
docker compose exec billing-app pytest tests/ -v
```

---

## Business Logic

### Rate Precedence
Provider-specific rates override global rates:
```
Example:
- Mandarin: 104 (scope: All)
- Mandarin: 120 (scope: 10001)

Provider 10001 → Uses rate 120
Provider 10002 → Uses rate 104
```

### Bill Calculation
```
For each delivery session:
1. Get truck from Weight service (GET /session/{id})
2. Filter sessions by provider's trucks
3. Skip sessions with neto = 'na' (truck not yet departed)
4. Group by product
5. Calculate: amount (kg) × rate (agorot) = pay
6. Sum all products = total
```

### Date Defaults
- **from**: 1st of current month at 00:00:00
- **to**: Current datetime

---

## Testing Strategy

Tests use mocked Weight service responses to ensure:
- ✅ Billing calculations are accurate
- ✅ Provider-specific rates work correctly
- ✅ Sessions with 'na' weights are skipped
- ✅ Only provider's trucks are included
- ✅ Error cases are handled properly

