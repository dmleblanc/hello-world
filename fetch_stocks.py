#!/usr/bin/env python3
"""
Stock Data Extraction Script

Fetches daily stock information from Yahoo Finance API based on a JSON configuration file.
Stocks are organized by categories (tech, agriculture, renewables, etc.).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yfinance as yf


def load_stocks_config(config_path: str) -> dict:
    """Load the stocks configuration from a JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "r") as f:
        return json.load(f)


def fetch_stock_data(ticker: str) -> dict:
    """Fetch daily stock data for a given ticker symbol."""
    stock = yf.Ticker(ticker)

    try:
        info = stock.info
        history = stock.history(period="1d")

        if history.empty:
            return {"error": "No data available"}

        latest = history.iloc[-1]

        return {
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open": round(latest["Open"], 2),
            "high": round(latest["High"], 2),
            "low": round(latest["Low"], 2),
            "close": round(latest["Close"], 2),
            "volume": int(latest["Volume"]),
            "market_cap": info.get("marketCap"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "currency": info.get("currency", "USD"),
        }
    except Exception as e:
        return {"error": str(e)}


def format_currency(value: float, currency: str = "USD") -> str:
    """Format a value as currency."""
    if value is None:
        return "N/A"
    if currency == "USD":
        return f"${value:,.2f}"
    return f"{value:,.2f} {currency}"


def format_large_number(value: int) -> str:
    """Format large numbers with abbreviations."""
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,}"


def print_stock_info(stock_name: str, ticker: str, data: dict) -> None:
    """Print formatted stock information."""
    if "error" in data:
        print(f"  {stock_name} ({ticker}): Error - {data['error']}")
        return

    price = data.get("current_price") or data.get("close")
    prev_close = data.get("previous_close")

    # Calculate change
    if price and prev_close:
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        change_str = f"{'+' if change >= 0 else ''}{change:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)"
    else:
        change_str = "N/A"

    currency = data.get("currency", "USD")

    print(f"\n  {stock_name} ({ticker})")
    print(f"    Price:        {format_currency(price, currency)} | Change: {change_str}")
    print(f"    Open:         {format_currency(data.get('open'), currency)} | Close: {format_currency(data.get('close'), currency)}")
    print(f"    High:         {format_currency(data.get('high'), currency)} | Low: {format_currency(data.get('low'), currency)}")
    print(f"    Volume:       {data.get('volume', 'N/A'):,}" if data.get('volume') else "    Volume:       N/A")
    print(f"    Market Cap:   {format_large_number(data.get('market_cap'))}")
    print(f"    52-Week:      High: {format_currency(data.get('52_week_high'), currency)} | Low: {format_currency(data.get('52_week_low'), currency)}")

    pe = data.get("pe_ratio")
    div_yield = data.get("dividend_yield")
    pe_str = f"{pe:.2f}" if pe else "N/A"
    div_str = f"{div_yield * 100:.2f}%" if div_yield else "N/A"
    print(f"    P/E Ratio:    {pe_str} | Dividend Yield: {div_str}")


def fetch_category_stocks(category_key: str, category_data: dict, verbose: bool = True) -> dict:
    """Fetch stock data for all stocks in a category."""
    category_name = category_data.get("name", category_key)
    stocks = category_data.get("stocks", [])

    if verbose:
        print(f"\n{'=' * 60}")
        print(f" {category_name.upper()}")
        print(f"{'=' * 60}")

    results = {}
    for stock in stocks:
        ticker = stock["ticker"]
        name = stock["name"]

        if verbose:
            print(f"\n  Fetching {ticker}...", end="", flush=True)

        data = fetch_stock_data(ticker)
        results[ticker] = {
            "name": name,
            "data": data
        }

        if verbose:
            print("\r" + " " * 30 + "\r", end="")  # Clear "Fetching" message
            print_stock_info(name, ticker, data)

    return results


def export_to_json(results: dict, output_path: str) -> None:
    """Export results to a JSON file."""
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "categories": results
    }

    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"\nResults exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch daily stock information from Yahoo Finance"
    )
    parser.add_argument(
        "-c", "--config",
        default="stocks.json",
        help="Path to the stocks configuration JSON file (default: stocks.json)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Export results to a JSON file"
    )
    parser.add_argument(
        "--category",
        help="Fetch only a specific category (e.g., tech, agriculture)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode - only output JSON (requires --output)"
    )

    args = parser.parse_args()

    if args.quiet and not args.output:
        print("Error: --quiet requires --output to be specified", file=sys.stderr)
        sys.exit(1)

    try:
        config = load_stocks_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    categories = config.get("categories", {})

    if args.category:
        if args.category not in categories:
            print(f"Error: Category '{args.category}' not found", file=sys.stderr)
            print(f"Available categories: {', '.join(categories.keys())}", file=sys.stderr)
            sys.exit(1)
        categories = {args.category: categories[args.category]}

    if not args.quiet:
        print(f"\n{'#' * 60}")
        print(f" DAILY STOCK DATA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#' * 60}")

    all_results = {}
    for category_key, category_data in categories.items():
        results = fetch_category_stocks(category_key, category_data, verbose=not args.quiet)
        all_results[category_key] = {
            "name": category_data.get("name", category_key),
            "stocks": results
        }

    if args.output:
        export_to_json(all_results, args.output)

    if not args.quiet:
        print(f"\n{'#' * 60}")
        print(" Fetch complete!")
        print(f"{'#' * 60}\n")


if __name__ == "__main__":
    main()
