"""Fetch the public contribution calendar and write it as JSON.

Scrapes the public HTML page rather than the GraphQL API: no token to manage,
so the workflow runs without a secret. The trade-off is that the markup can
change, hence the sanity checks at the end. A red workflow beats an empty
calendar committed in silence.

Usage: python scripts/fetch_contributions.py <username> [destination]
"""

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://github.com/users/{user}/contributions"
TIMEOUT = 30
MIN_WEEKS = 51
MIN_DAYS = 360

COUNT_RE = re.compile(r"^(No|\d+)\s+contribution")


def parse_count(tooltip_text: str) -> int:
    """Pull the contribution count out of the tooltip text."""
    match = COUNT_RE.match(tooltip_text.strip())
    if not match:
        return 0
    return 0 if match.group(1) == "No" else int(match.group(1))


def fetch(username: str) -> dict:
    response = requests.get(
        URL.format(user=username),
        headers={
            "Accept": "text/html",
            "User-Agent": f"{username}-profile-art/1.0",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        raise SystemExit(
            "no ContributionCalendar-day cell found: "
            "GitHub markup has most likely changed"
        )

    tooltips = {
        tip.get("for"): tip.get_text(strip=True)
        for tip in soup.find_all("tool-tip")
        if tip.get("for")
    }

    weeks: dict[int, list] = {}
    for cell in cells:
        date = cell.get("data-date")
        cell_id = cell.get("id") or ""
        if not date or not cell_id:
            continue
        # id = contribution-day-component-<weekday>-<week>
        parts = cell_id.rsplit("-", 2)
        if len(parts) != 3:
            continue
        weekday, week = int(parts[1]), int(parts[2])
        weeks.setdefault(week, []).append(
            {
                "date": date,
                "weekday": weekday,
                "level": int(cell.get("data-level", 0)),
                "count": parse_count(tooltips.get(cell_id, "")),
            }
        )

    ordered = [
        sorted(weeks[w], key=lambda d: d["weekday"]) for w in sorted(weeks)
    ]
    days = [day for week in ordered for day in week]

    # Sanity guards: without them a markup change produces an empty payload
    # that the workflow would happily commit as a valid calendar.
    if len(ordered) < MIN_WEEKS:
        raise SystemExit(f"only {len(ordered)} weeks parsed, expected >= {MIN_WEEKS}")
    if len(days) < MIN_DAYS:
        raise SystemExit(f"only {len(days)} days parsed, expected >= {MIN_DAYS}")

    return {
        "username": username,
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "total": sum(d["count"] for d in days),
        "weeks": ordered,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: fetch_contributions.py <username> [destination]")
    user = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/contributions.json")
    payload = fetch(user)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"wrote {out}: {len(payload['weeks'])} weeks, "
        f"{payload['total']} contributions, {payload['from']} -> {payload['to']}"
    )
