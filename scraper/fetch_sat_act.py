import datetime
from pathlib import Path
from generate_ics import generate_all

def fetch_sat_data():
    # TODO: replace with real scraping
    tests = [
        {
            "test_date": datetime.date(2026, 3, 14),
            "reg_deadline": datetime.date(2026, 2, 7),
            "late_deadline": datetime.date(2026, 2, 24),
        },
    ]
    sat_data = []
    for t in tests:
        label = t["test_date"].strftime("%B %d, %Y")
        sat_data.append({"date": t["test_date"], "type": "test", "label": "SAT", "test_label": label})
        sat_data.append({"date": t["reg_deadline"], "type": "reg_deadline", "label": "SAT", "test_label": label})
        sat_data.append({"date": t["late_deadline"], "type": "late_deadline", "label": "SAT", "test_label": label})
    return sat_data

def fetch_act_data():
    # TODO: replace with real scraping
    tests = [
        {
            "test_date": datetime.date(2026, 4, 4),
            "reg_deadline": datetime.date(2026, 2, 28),
            "late_deadline": datetime.date(2026, 3, 13),
        },
    ]
    act_data = []
    for t in tests:
        label = t["test_date"].strftime("%B %d, %Y")
        act_data.append({"date": t["test_date"], "type": "test", "label": "ACT", "test_label": label})
        act_data.append({"date": t["reg_deadline"], "type": "reg_deadline", "label": "ACT", "test_label": label})
        act_data.append({"date": t["late_deadline"], "type": "late_deadline", "label": "ACT", "test_label": label})
    return act_data

def main():
    sat_data = fetch_sat_data()
    act_data = fetch_act_data()
    public_dir = Path(__file__).resolve().parents[1] / "public"
    generate_all(sat_data, act_data, public_dir)

if __name__ == "__main__":
    main()
