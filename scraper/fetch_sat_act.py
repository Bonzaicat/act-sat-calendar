"""
Scrape SAT and ACT test dates, registration deadlines, and late deadlines
from the College Board and ACT websites, then generate ICS calendar files.
"""

import datetime
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from generate_ics import generate_all

# ── URLs ────────────────────────────────────────────────────────────────────
SAT_URL = "https://satsuite.collegeboard.org/sat/dates-deadlines"
ACT_URL = (
    "https://www.act.org/content/act/en/"
    "products-and-services/the-act/registration/test-dates.html"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Date parsing helpers ────────────────────────────────────────────────────

# Handles both abbreviated ("Aug.", "Sept.") and full ("August", "September")
MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Matches patterns like "June 6, 2026", "Aug. 7, 2026", "May 22"
DATE_RE = re.compile(
    r"([A-Za-z]+)\.?\s+(\d{1,2})(?:,?\s+(\d{4}))?",
)


def parse_date(text: str, fallback_year: int | None = None) -> datetime.date | None:
    """Parse a date string into a datetime.date.

    Supports formats like:
        "June 6, 2026"
        "Aug. 7, 2026"
        "May 22"          (year inferred from fallback_year)
    """
    text = text.strip()
    m = DATE_RE.search(text)
    if not m:
        return None
    month_str = m.group(1).lower().rstrip(".")
    day = int(m.group(2))
    year = int(m.group(3)) if m.group(3) else fallback_year
    month = MONTH_MAP.get(month_str)
    if month is None or year is None:
        return None
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def clean_cell(cell) -> str:
    """Extract clean text from a table cell, stripping links and footnotes."""
    # Remove footnote markers like * and **
    text = cell.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Strip asterisks used as footnote markers
    text = text.strip("* ")
    return text


# ── SAT scraper ─────────────────────────────────────────────────────────────

def fetch_sat_data() -> list[dict]:
    """Scrape SAT test dates and deadlines from College Board."""
    print(f"Fetching SAT data from {SAT_URL}")
    resp = requests.get(SAT_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    sat_data = []
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue

            cell_texts = [clean_cell(c) for c in cells]

            # The first column is the test date; skip header rows and
            # footnote rows that don't start with a month name.
            test_date = parse_date(cell_texts[0])
            if test_date is None:
                continue

            reg_deadline = parse_date(cell_texts[1], fallback_year=test_date.year)
            late_deadline = parse_date(cell_texts[2], fallback_year=test_date.year)

            # If the deadline month is after the test month, it belongs
            # to the previous year (shouldn't happen for SAT, but be safe).
            if reg_deadline and reg_deadline > test_date:
                reg_deadline = reg_deadline.replace(year=reg_deadline.year - 1)
            if late_deadline and late_deadline > test_date:
                late_deadline = late_deadline.replace(year=late_deadline.year - 1)

            label = test_date.strftime("%B %d, %Y")
            sat_data.append(
                {"date": test_date, "type": "test", "label": "SAT", "test_label": label}
            )
            if reg_deadline:
                sat_data.append(
                    {"date": reg_deadline, "type": "reg_deadline", "label": "SAT", "test_label": label}
                )
            if late_deadline:
                sat_data.append(
                    {"date": late_deadline, "type": "late_deadline", "label": "SAT", "test_label": label}
                )

    print(f"  Found {len([e for e in sat_data if e['type'] == 'test'])} SAT test dates")
    return sat_data


# ── ACT scraper ─────────────────────────────────────────────────────────────

def fetch_act_data() -> list[dict]:
    """Scrape ACT test dates and deadlines from act.org."""
    print(f"Fetching ACT data from {ACT_URL}")
    resp = requests.get(ACT_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    act_data = []
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            # ACT table: Test Date | Reg Deadline | Late Deadline | Photo/Standby | Score Release
            if len(cells) < 3:
                continue

            cell_texts = [clean_cell(c) for c in cells]

            test_date = parse_date(cell_texts[0])
            if test_date is None:
                continue

            reg_deadline = parse_date(cell_texts[1], fallback_year=test_date.year)
            late_deadline = parse_date(cell_texts[2], fallback_year=test_date.year)

            # ACT deadline columns sometimes omit the year.  If the inferred
            # deadline ends up *after* the test date, push it back one year.
            if reg_deadline and reg_deadline > test_date:
                reg_deadline = reg_deadline.replace(year=reg_deadline.year - 1)
            if late_deadline and late_deadline > test_date:
                late_deadline = late_deadline.replace(year=late_deadline.year - 1)

            label = test_date.strftime("%B %d, %Y")
            act_data.append(
                {"date": test_date, "type": "test", "label": "ACT", "test_label": label}
            )
            if reg_deadline:
                act_data.append(
                    {"date": reg_deadline, "type": "reg_deadline", "label": "ACT", "test_label": label}
                )
            if late_deadline:
                act_data.append(
                    {"date": late_deadline, "type": "late_deadline", "label": "ACT", "test_label": label}
                )

    print(f"  Found {len([e for e in act_data if e['type'] == 'test'])} ACT test dates")
    return act_data


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    sat_data = fetch_sat_data()
    act_data = fetch_act_data()

    if not sat_data:
        print("WARNING: No SAT dates found — page structure may have changed", file=sys.stderr)
    if not act_data:
        print("WARNING: No ACT dates found — page structure may have changed", file=sys.stderr)

    public_dir = Path(__file__).resolve().parents[1] / "public"
    generate_all(sat_data, act_data, public_dir)
    print(f"ICS files written to {public_dir}")


if __name__ == "__main__":
    main()
