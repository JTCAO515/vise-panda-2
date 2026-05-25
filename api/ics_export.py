"""Generate .ics calendar files from trip itineraries."""

def generate_ics(trip: dict) -> str:
    """
    Generate iCalendar (.ics) content from a trip dict.

    trip format:
    {
        "title": "Beijing 3-day trip",
        "start_date": "2026-06-01",
        "end_date": "2026-06-03",
        "itinerary": [
            {"day": 1, "date": "2026-06-01", "activities": [...], "hotel": "..."},
            ...
        ]
    }
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//VisePanda//Travel Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:VisePanda Trip",
        "X-WR-TIMEZONE:Asia/Shanghai"
    ]

    uid_base = str(abs(hash(trip.get("title", "trip"))))

    for day in trip.get("itinerary", []):
        date_str = day.get("date", trip.get("start_date", ""))
        if not date_str:
            continue

        day_num = day.get("day", 1)

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid_base}-day{day_num}@visepanda")
        lines.append(f"DTSTART;VALUE=DATE:{date_str.replace('-','')}")
        lines.append(f"DTEND;VALUE=DATE:{date_str.replace('-','')}")
        lines.append(f"SUMMARY:Day {day_num} - {trip.get('title', 'Trip')}")

        activities = day.get("activities", [])
        hotel = day.get("hotel", "")

        desc_parts = []
        if activities:
            desc_parts.append("Activities:")
            for act in activities:
                desc_parts.append(f"- {act.get('time','')} {act.get('name','')}")
        if hotel:
            desc_parts.append(f"\\nHotel: {hotel}")

        sep = "\\n"
        lines.append(f"DESCRIPTION:{sep.join(desc_parts)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
