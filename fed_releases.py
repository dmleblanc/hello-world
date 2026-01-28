#!/usr/bin/env python3
"""
Federal Reserve Planned Releases Fetcher

This script fetches planned releases from the Federal Reserve Economic Data (FRED) API.
"""

import requests
from datetime import datetime, timedelta


FRED_API_KEY = "c85a9b1f804a599557f9ce3f1ed42ac8"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"


def get_releases(limit=100):
    """Fetch all releases from FRED API."""
    url = f"{FRED_BASE_URL}/releases"
    params = {
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": limit,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("releases", [])


def get_release_dates(include_release_dates_with_no_data=True, limit=100):
    """Fetch upcoming release dates from FRED API."""
    url = f"{FRED_BASE_URL}/releases/dates"

    # Get dates from today onwards
    today = datetime.now().strftime("%Y-%m-%d")

    params = {
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "realtime_start": today,
        "include_release_dates_with_no_data": str(include_release_dates_with_no_data).lower(),
        "limit": limit,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("release_dates", [])


def get_release_info(release_id):
    """Fetch detailed information about a specific release."""
    url = f"{FRED_BASE_URL}/release"
    params = {
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "release_id": release_id,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    releases = response.json().get("releases", [])
    return releases[0] if releases else None


def assemble_planned_releases():
    """Assemble and display planned Federal Reserve releases."""
    print("=" * 70)
    print("FEDERAL RESERVE PLANNED RELEASES")
    print("=" * 70)
    print()

    # Fetch upcoming release dates
    print("Fetching upcoming release dates...")
    release_dates = get_release_dates(limit=50)

    if not release_dates:
        print("No upcoming releases found.")
        return []

    # Group releases by date
    releases_by_date = {}
    for rd in release_dates:
        date = rd.get("date", "Unknown")
        release_id = rd.get("release_id")
        release_name = rd.get("release_name", "Unknown Release")

        if date not in releases_by_date:
            releases_by_date[date] = []

        releases_by_date[date].append({
            "release_id": release_id,
            "release_name": release_name,
        })

    # Display releases grouped by date
    print(f"\nFound {len(release_dates)} upcoming releases:\n")
    print("-" * 70)

    for date in sorted(releases_by_date.keys()):
        print(f"\n{date}")
        print("-" * 40)
        for release in releases_by_date[date]:
            print(f"  - [{release['release_id']}] {release['release_name']}")

    print("\n" + "=" * 70)
    print(f"Total: {len(release_dates)} planned releases")
    print("=" * 70)

    return release_dates


def list_all_releases():
    """List all available FRED releases."""
    print("=" * 70)
    print("ALL FEDERAL RESERVE DATA RELEASES")
    print("=" * 70)
    print()

    releases = get_releases(limit=200)

    if not releases:
        print("No releases found.")
        return []

    print(f"Found {len(releases)} releases:\n")
    print(f"{'ID':<8} {'Name':<50} {'Link'}")
    print("-" * 70)

    for release in releases:
        release_id = release.get("id", "N/A")
        name = release.get("name", "Unknown")[:48]
        link = release.get("link", "")
        print(f"{release_id:<8} {name:<50} {link[:30]}")

    return releases


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch planned releases from the Federal Reserve (FRED API)"
    )
    parser.add_argument(
        "--list-all",
        action="store_true",
        help="List all available releases instead of just planned ones"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of releases to fetch (default: 50)"
    )

    args = parser.parse_args()

    try:
        if args.list_all:
            list_all_releases()
        else:
            assemble_planned_releases()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from FRED API: {e}")
        return 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
