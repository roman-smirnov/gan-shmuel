# 🏋️‍♂️ Weight Service  
A Reliable Industrial Weighing Microservice for the Gan Shmuel Project

The **Weight Service** manages the full weighing workflow for trucks and containers in an industrial environment.  
It supports IN/OUT weighing, NET calculation, session tracking, container management, time-based queries, and batch uploads —  
and fully complies with the official Gan Shmuel API specification.

---

## 🚀 Features Overview

### 📦 Weighing Logic
- **IN** → Gross weight  
- **OUT** → Tare weight  
- **NONE** → Standalone container weighing  
- Automatic NET calculation:  
- Handles incomplete container data safely (`"na"`)

---
NET = BRUTO - TRUCK_TARA - Σ(container_tara)

### 🧺 Container Management
- Batch upload of container tare weights (CSV / JSON)
- Automatic kg/lbs unit handling
- Tracking of unknown containers

---

### 🗂 Session Tracking
Each weighing generates a consistent session record:
- `id`
- `truck` or `"na"`
- `direction`
- `bruto`
- `truckTara` (OUT only)
- `neto` or `"na"`
- `timestamp`
- `produce`
- `containers` list

---

## 🔌 REST API Endpoints

| Method | Route | Description |
|--------|--------|-------------|
| `POST` | `/weight` | IN/OUT/NONE weighing flow, NET calculation, force-logic |
| `POST` | `/batch-weight` | Upload container tare weights (CSV/JSON) |
| `GET` | `/unknown` | List all containers missing tare |
| `GET` | `/weight` | Time & direction filtered weighings |
| `GET` | `/item/<id>` | Truck/container details + sessions |
| `GET` | `/session/<id>` | Full weighing session result |
| `GET` | `/health` | Service health + DB status |

---

# 📘 API Compliance Summary  
### _(Full alignment with the Gan Shmuel official Weight API specification)_

### ✔ `POST /weight`
- Supports `in`, `out`, `none`  
- Validates truck IDs or `"na"`  
- Accepts comma-separated containers  
- Stores `bruto`, `truckTara`, `neto`  
- Implements the required force-logic:  
- IN→IN (error unless `force=true`)  
- OUT→OUT (error unless `force=true`)  
- OUT without IN (error)  
- NONE after IN (error)  
- Returns session in the exact required structure

---

### ✔ `POST /batch-weight`
- Accepts formats:  
- CSV (`id,kg` or `id,lbs`)  
- JSON (`[{id, weight, unit}, ...]`)
- Loads files from `/in`
- Overwrites existing container tares when needed

---

### ✔ `GET /unknown`
- Returns a list of containers with missing tare weight

---

### ✔ `GET /weight?from=&to=&filter=`
- Supports date range filtering (yyyymmddhhmmss)
- Supports direction filtering (`in,out,none`)
- Returns session objects (no batch records)

---

### ✔ `GET /item/<id>`

Returns:

```json
{
  "id": "<str>",
  "tara": "<int or \"na\">",
  "sessions": ["s1", "s2", "..."]
}

GET /session/<id>
{
  "id": "<str>",
  "truck": "<id or 'na'>",
  "bruto": <int>,
  "truckTara": <int>, // OUT only
  "neto": <int or 'na'>
}
```
+----------------------------+
|      Weight API (Flask)    |
+--------------+-------------+
               |
               v
+----------------------------+
|        MySQL weightdb      |
+----------------------------+
🧪 Testing

Unit tests – weighing logic, container rules

Integration tests – DB interactions

E2E tests – IN → OUT → NET → GET /session

🐳 Docker & DevOps

Dockerfile included

docker-compose with MySQL + healthcheck

.env configuration

Persistent volume for DB

Service waits for DB to become healthy before starting

🎯 Why This Service Matters

Accurate NET weight is essential for provider payment and factory automation.
This microservice ensures reliable, traceable, and consistent weighing —
forming the foundation for Billing and production analytics.
