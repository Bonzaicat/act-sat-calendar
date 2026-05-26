import datetime
from uuid import uuid4
from pathlib import Path

def format_date(d):
    return d.strftime("%Y%m%d")

def ics_header():
    return [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//bonzaicat//SAT-ACT Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

def ics_footer():
    return ["END:VCALENDAR"]

def make_event(summary, date, description=None):
    dtstamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    uid = f"{uuid4()}@bonzaicat-sat-act"
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{format_date(date)}",
        f"DTEND;VALUE=DATE:{format_date(date + datetime.timedelta(days=1))}",
        f"SUMMARY:{summary}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{description}")
    lines.append("END:VEVENT")
    return lines

def build_cal(events):
    lines = ics_header()
    for ev in events:
        lines.extend(ev)
    lines.extend(ics_footer())
    return "\r\n".join(lines) + "\r\n"

def write_ics(path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_cal(events), encoding="utf-8")

def generate_all(sat_data, act_data, public_dir):
    sat_events = []
    act_events = []
    combined_events = []

    # SAT
    for item in sat_data:
        d = item["date"]
        if item["type"] == "test":
            summary = "SAT Test Date"
            desc = d.strftime("SAT national test date on %B %d, %Y")
        elif item["type"] == "reg_deadline":
            summary = f"Registration Deadline for {item['test_label']} SAT"
            desc = f"Regular registration deadline for {item['test_label']} SAT ({d.strftime('%B %d, %Y')})"
        elif item["type"] == "late_deadline":
            summary = f"Late Registration Deadline for {item['test_label']} SAT"
            desc = f"Late registration deadline for {item['test_label']} SAT ({d.strftime('%B %d, %Y')})"
        else:
            continue
        ev = make_event(summary, d, desc)
        sat_events.append(ev)
        combined_events.append(ev)

    # ACT
    for item in act_data:
        d = item["date"]
        if item["type"] == "test":
            summary = "ACT Test Date"
            desc = d.strftime("ACT national test date on %B %d, %Y")
        elif item["type"] == "reg_deadline":
            summary = f"Registration Deadline for {item['test_label']} ACT"
            desc = f"Regular registration deadline for {item['test_label']} ACT ({d.strftime('%B %d, %Y')})"
        elif item["type"] == "late_deadline":
            summary = f"Late Registration Deadline for {item['test_label']} ACT"
            desc = f"Late registration deadline for {item['test_label']} ACT ({d.strftime('%B %d, %Y')})"
        else:
            continue
        ev = make_event(summary, d, desc)
        act_events.append(ev)
        combined_events.append(ev)

    public = Path(public_dir)
    write_ics(public / "sat.ics", sat_events)
    write_ics(public / "act.ics", act_events)
    write_ics(public / "combined.ics", combined_events)

if __name__ == "__main__":
    today = datetime.date.today()
    sat_sample = [
        {
            "date": today,
            "type": "test",
            "label": "SAT",
            "test_label": today.strftime("%B %d, %Y"),
        },
    ]
    act_sample = []
    generate_all(sat_sample, act_sample, "public")
