import uuid
from fastapi import APIRouter, HTTPException
from api.models.watchlist import WatchlistAddRequest

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

# In-memory store for Day 1 MVP. Replace with a DB (PostgreSQL/Redis) in later sprints.
# Structure: { user_id: [ { symbol, watchlist_id } ] }
_watchlist_store: dict[str, list[dict]] = {}


@router.post("")
def add_to_watchlist(body: WatchlistAddRequest):
    """
    Add a stock symbol to a user's watchlist.
    """
    user_id = body.user_id
    symbol = body.symbol.upper()

    user_list = _watchlist_store.setdefault(user_id, [])

    # Prevent duplicates
    if any(item["symbol"] == symbol for item in user_list):
        raise HTTPException(
            status_code=409,
            detail=f"{symbol} is already in your watchlist."
        )

    watchlist_id = f"wl_{uuid.uuid4().hex[:8]}"
    user_list.append({"symbol": symbol, "watchlist_id": watchlist_id})

    return {
        "message": f"{symbol} successfully added to watchlist.",
        "watchlist_id": watchlist_id,
        "status": "success",
    }


@router.get("/{user_id}")
def get_watchlist(user_id: str):
    """
    Retrieve all stocks in a user's watchlist.
    """
    user_list = _watchlist_store.get(user_id, [])

    return {
        "user_id": user_id,
        "count": len(user_list),
        "watchlist": user_list,
        "status": "success",
    }


@router.delete("/{user_id}/{symbol}")
def remove_from_watchlist(user_id: str, symbol: str):
    """
    Remove a specific stock symbol from a user's watchlist.
    """
    symbol = symbol.upper()
    user_list = _watchlist_store.get(user_id, [])
    original_len = len(user_list)

    updated = [item for item in user_list if item["symbol"] != symbol]

    if len(updated) == original_len:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} was not found in user '{user_id}' watchlist."
        )

    _watchlist_store[user_id] = updated

    return {
        "message": f"{symbol} removed from watchlist.",
        "status": "success",
    }
