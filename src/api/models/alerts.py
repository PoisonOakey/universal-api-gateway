from pydantic import BaseModel
from typing import Literal


class PatternAlertRequest(BaseModel):
    user_id: str
    symbol: str
    pattern_type: Literal[
        "golden_cross",
        "death_cross",
        "mean_reversion",
        "breakout",
        "rsi_overbought",
        "rsi_oversold",
    ]
    sensitivity: Literal["low", "medium", "high"] = "medium"


class PatternAlertResponse(BaseModel):
    alert_id: str
    message: str
    status: str
