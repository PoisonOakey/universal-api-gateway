import uuid
from fastapi import APIRouter, HTTPException
from api.models.alerts import PatternAlertRequest

router = APIRouter(prefix="/pattern-alerts", tags=["Pattern Alerts"])

# In-memory store for Day 1 MVP. Replace with a persistent DB + background task queue later.
# Structure: { alert_id: { user_id, symbol, pattern_type, sensitivity } }
_alert_store: dict[str, dict] = {}


@router.post("")
def set_pattern_alert(body: PatternAlertRequest):
    """
    Register a pattern-based alert for a stock.
    The system will notify the user when the specified algorithmic
    pattern (e.g. golden_cross, breakout) is detected.
    """
    alert_id = f"alert_{uuid.uuid4().hex[:8]}"

    _alert_store[alert_id] = {
        "user_id": body.user_id,
        "symbol": body.symbol.upper(),
        "pattern_type": body.pattern_type,
        "sensitivity": body.sensitivity,
        "status": "active",
    }

    return {
        "alert_id": alert_id,
        "message": (
            f"Pattern alert set. You will be notified when "
            f"{body.symbol.upper()} exhibits a '{body.pattern_type}' pattern."
        ),
        "status": "success",
    }


@router.get("/{user_id}")
def get_user_alerts(user_id: str):
    """
    Retrieve all active pattern alerts for a given user.
    """
    user_alerts = [
        {"alert_id": aid, **data}
        for aid, data in _alert_store.items()
        if data["user_id"] == user_id
    ]

    return {
        "user_id": user_id,
        "count": len(user_alerts),
        "alerts": user_alerts,
        "status": "success",
    }


@router.delete("/{alert_id}")
def cancel_alert(alert_id: str):
    """
    Cancel and remove an active pattern alert by its ID.
    """
    if alert_id not in _alert_store:
        raise HTTPException(
            status_code=404,
            detail=f"Alert '{alert_id}' not found."
        )

    removed = _alert_store.pop(alert_id)

    return {
        "message": (
            f"Alert for {removed['symbol']} ({removed['pattern_type']}) "
            "has been cancelled."
        ),
        "status": "success",
    }
