from fastapi import APIRouter, HTTPException, Query
import yfinance as yf

router = APIRouter(prefix="/stock", tags=["Stocks"])


@router.get("/{symbol}")
def get_stock_value(symbol: str):
    """
    Fetch current market price and core metrics for a given ticker symbol.
    Uses yfinance fast_info for a lightweight, quick response.
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.fast_info

        current_price = info.last_price
        currency = info.currency

        if current_price is None:
            raise HTTPException(
                status_code=404,
                detail=f"No price data found for symbol '{symbol.upper()}'. "
                       "Check if the ticker is valid."
            )

        return {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            "currency": currency,
            "market_cap": info.market_cap,
            "day_high": info.day_high,
            "day_low": info.day_low,
            "volume": info.three_month_average_volume,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/history")
def get_stock_history(
    symbol: str,
    period: str = Query(
        default="1mo",
        description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max",
    ),
):
    """
    Retrieve OHLCV (Open/High/Low/Close/Volume) historical data for a given symbol.
    Used to render candlestick or line charts on the frontend.
    """
    valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}

    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Valid options: {sorted(valid_periods)}",
        )

    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for symbol '{symbol.upper()}'."
            )

        history = [
            {
                "date": str(index.date()),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            }
            for index, row in hist.iterrows()
        ]

        return {
            "symbol": symbol.upper(),
            "period": period,
            "count": len(history),
            "history": history,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
