# Financial API Documentation

---

## 1. API Architecture & Calling Mechanism

**Overview:**
This API acts as a middleware connecting your frontend to Yahoo Finance (`yfinance`) market data. Following the Minimum Viable Architecture plan, it is built using **Python and the FastAPI framework**, providing standard HTTP CRUD methods to interact with stock metrics.

**How to call the API:**
- **Protocol:** HTTP/HTTPS REST API
- **Methods:** `GET` (fetch data), `POST` (create data), `PUT` (update), `DELETE` (remove).
- **Data Format:** JSON for both requests and responses.
- **Client Implementation:** Can be called via `fetch()` in frontend apps, `requests` in Python scripts, or standard HTTP clients like Postman.

---

## 2. API #1: Get Stock Value

**Functionality:** Retrieves the current market value and core metrics for a specific stock to prevent staring at stock prices all day.

**REST Endpoint:** `GET /api/v1/stock/{symbol}`

**Input (Path Parameter):**
- `symbol` (string): The ticker symbol of the desired stock (e.g., `AAPL`, `TSLA`).

**Output (JSON Response):**
```json
{
  "symbol": "AAPL",
  "current_price": 150.25,
  "currency": "USD",
  "status": "success"
}
```

**Implementation Note:** Uses `yfinance` in the Python backend to fetch market data and format it into JSON.

---

## 3. API #2: Add to Watchlist (Keep Track)

**Functionality:** Keeps track of interested stocks by adding them to a user's wishlist or portfolio cart.

**REST Endpoint:** `POST /api/v1/watchlist`

**Input (JSON Body):**
```json
{
  "user_id": "user_123",
  "symbol": "AAPL"
}
```

**Output (JSON Response):**
```json
{
  "message": "AAPL successfully added to watchlist.",
  "watchlist_id": "wl_789",
  "status": "success"
}
```

---

## 4. API #3: Set Pattern-Based Alert

**Functionality:** Instead of a basic static price threshold, this endpoint allows the user to subscribe to specific technical or physics-economic patterns (e.g., "golden_cross", "mean_reversion", "breakout"). When the underlying algorithmic pattern is detected for the stock, the system will trigger an alert for trading.

**REST Endpoint:** `POST /api/v1/pattern-alerts`

**Input (JSON Body):**
```json
{
  "user_id": "user_123",
  "symbol": "AAPL",
  "pattern_type": "golden_cross",
  "sensitivity": "medium"
}
```
*(Pattern types represent the algorithmic phenomena to detect)*

**Output (JSON Response):**
```json
{
  "alert_id": "alert_pattern_9912",
  "message": "Pattern alert set. You will be notified when AAPL exhibits a golden_cross pattern.",
  "status": "success"
}
```

---

## 5. API #4: Get Historical Data (For Charts)

**Functionality:** Retrieves a timeseries of past stock prices to be used by the frontend for rendering candlestick or line charts, which is essential for visually validating pattern alerts.

**REST Endpoint:** `GET /api/v1/stock/{symbol}/history`

**Input (Query Parameters):**
- `period` (string, optional): E.g., `1d`, `1mo`, `1y` (default: `1mo`).

**Output (JSON Response):**
```json
{
  "symbol": "AAPL",
  "history": [
    {"date": "2026-07-01", "close": 149.50},
    {"date": "2026-07-02", "close": 150.25}
  ],
  "status": "success"
}
```

---

## 6. REST Endpoint Summary

| Endpoint | Method | Purpose | Payload/Params |
| :--- | :--- | :--- | :--- |
| `/api/v1/stock/{symbol}` | **GET** | Fetch current stock value | Param: `symbol` (e.g., AAPL) |
| `/api/v1/watchlist` | **POST** | Add stock to track/wishlist | Body: `user_id`, `symbol` |
| `/api/v1/watchlist/{user_id}` | **GET** | View user's watchlist | Param: `user_id` |
| `/api/v1/watchlist/{symbol}` | **DELETE** | Remove stock from watchlist | Param: `symbol` |
| `/api/v1/pattern-alerts` | **POST** | Set pattern-based alert | Body: `user_id`, `symbol`, `pattern_type`, `sensitivity` |
| `/api/v1/pattern-alerts/{alert_id}` | **DELETE** | Cancel an active alert | Param: `alert_id` |
