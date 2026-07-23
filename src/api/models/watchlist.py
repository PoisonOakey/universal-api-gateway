from pydantic import BaseModel
from typing import Literal


class WatchlistAddRequest(BaseModel):
    user_id: str
    symbol: str


class WatchlistResponse(BaseModel):
    message: str
    watchlist_id: str
    status: str


class WatchlistItem(BaseModel):
    symbol: str
    watchlist_id: str
