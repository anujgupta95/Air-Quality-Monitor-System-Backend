# 🌫️ Air Quality Monitor System [Backend]

**Deployed URL:** 🔗 [https://sih.anujg.me](https://sih.anujg.me)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/REST%20API-FF6F00?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/CORS-enabled-green?style=for-the-badge"/>
</p>

---

## 📝 Description

This is the backend system for an **Air Quality Monitoring & Health Advisory Platform**. It fetches and stores real-time air quality data and sensor readings, provides RESTful API endpoints for clients, and uses Gemini (LLM) to generate health advice based on AQI and health conditions.

---

## 🚀 Features

- ✅ Real-time and historical AQI data fetch from 3rd-party APIs
- ✅ IoT sensor data ingestion (WiFi-based) and MongoDB storage
- ✅ CSV export for sensor data by device ID
- ✅ Health advice generation using Gemini LLM
- ✅ RESTful Blog CRUD API (demo purposes)
- ✅ In-memory caching with Flask-Caching
- ✅ CORS-enabled API
- ✅ Discord notifications for data ingestion

---

## 🌐 API Endpoints

### 🔹 Health Check
```http
GET /
→ Returns: "Hello, World!"
````

### 🔹 Sensor Data Ingestion

```http
POST /sensor/wifi
Body (JSON):
{
  "deviceID": "sensor-123",
  "temp": 30,
  "humidity": 50,
  "pm": 120,
  ...
}
→ Saves to MongoDB in a collection named after deviceID
```

### 🔹 Retrieve Sensor History

```http
GET /fetch/hw/<deviceID>
→ Returns latest 15 sensor readings for a device
```

### 🔹 Export Sensor Data (CSV)

```http
GET /csv/hw/<deviceID>
→ Returns downloadable CSV file of all readings
```

### 🔹 Get Real-Time AQI Data

```http
GET /fetch/<city>
→ Returns live AQI data for a city (cached)
```

### 🔹 Get Historical AQI (30 Days)

```http
GET /fetch/<city>/history
→ Returns past month’s AQI stats from aqi.in API
```

### 🔹 Generate Health Advice via Gemini

```http
POST /gemini
Body (JSON):
{
  "city": "Delhi",
  "aqi": 180,
  "health_issues": "asthma, allergy"
}
→ Returns Markdown-formatted health tips using Gemini
```

### 🔹 Blog CRUD API

* `GET /blogs` → List all blogs
* `GET /blogs/<blog_id>` → Get blog by ID
* `POST /blogs` → Create a new blog
* `PUT /blogs/<blog_id>` → Update existing blog
* `DELETE /blogs/<blog_id>` → Delete a blog

---

## ⚙️ Setup & Installation

### 📁 Clone Repository

```bash
git clone https://github.com/anujgupta95/Air-Quality-Monitor-System-Backend.git
```

### 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

### 🧪 Create `.env` File

```env
API_URL=https://api.waqi.info/feed/
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
DB_NAME=air_quality
AUTH_TOKEN=<WAQI_API_TOKEN>
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
DISCORD_WEBHOOK=<DISCORD_WEBHOOK_URL>
```

### 🚀 Run Server

```bash
flask run
# or
python api/index.py
```

---

## 🧠 Caching & Performance

* Simple in-memory cache via `Flask-Caching`
* City AQI data is cached to minimize API calls
* Supports rapid sensor writes without performance drop (MongoDB)

---

## 🧑‍💻 Developer Notes

* All sensors write to a MongoDB collection named after their `deviceID`

* To test Gemini health advisory:

  ```bash
  curl -X POST http://localhost:5000/gemini -H "Content-Type: application/json" -d '{"city":"Delhi", "aqi":180, "health_issues":"asthma"}'
  ```

* Discord webhook triggers on data ingest for alerting/logging (optional)

---

## 📬 Contact

For queries or contributions, connect via [anujg.me](https://anujg.me) or raise an issue.
