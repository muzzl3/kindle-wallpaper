from icalendar import Calendar
import recurring_ical_events
import datetime
from datetime import timedelta
import urllib.request
import time
import codecs
from itertools import groupby
import json
import sys
import zoneinfo

# Load settings from settings.json
try:
    # The script is run from 'In the server/' so the path is relative to that
    with open('settings.json', 'r') as f:
        settings = json.load(f)
        ICAL_URL = settings['ICAL_URL']
except FileNotFoundError:
    print("Error: settings.json not found in 'In the server/'. Please create it based on settings.json.example.", file=sys.stderr)
    exit(1)
except KeyError:
    print("Error: ICAL_URL not found in settings.json.", file=sys.stderr)
    exit(1)

def generate_svg_for_page(events, filename):
    """Generates an SVG file for a given list of events and returns the overflow."""
    if not events:
        # Create a blank SVG if there are no events
        blank_svg = '<svg width="600" height="800" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans"></svg>'
        codecs.open(filename, 'w', encoding='utf-8').write(blank_svg)
        return []

    # --- Dynamically calculate spacing ---
    grouped_events = [list(g) for k, g in groupby(events, key=lambda e: e['start_date'])]
    num_days = len(grouped_events)
    num_events = len(events)

    svg_height = 800
    top_margin = 50
    bottom_margin = 20
    available_height = svg_height - top_margin - bottom_margin

    y_increment_px = 40
    if num_days > 0 or num_events > 0:
        # A day header takes up 1.2 units, and the space after a day takes 0.5 units. An event takes 1 unit.
        total_units = (num_days * 1.2) + num_events + (num_days * 0.5)
        if total_units > 0:
            calculated_increment = available_height / total_units
            # Ensure the increment is not so small that text overlaps
            min_increment = 21
            y_increment_px = max(calculated_increment, min_increment)

    # --- Generate SVG content and identify overflow ---
    svg_elements = []
    y_px = float(top_margin)
    x_px = 20
    x_name_offset = 260

    overflow_events = []
    is_overflow = False
    
    grouped_events_iter = iter(grouped_events)

    for day_events in grouped_events_iter:
        if not day_events:
            continue
        
        day = day_events[0]['start_date']
        
        # Check if header and at least one event can theoretically fit
        header_plus_event_height = (y_increment_px * 1.2) + y_increment_px
        if not is_overflow and y_px + header_plus_event_height > svg_height - bottom_margin:
            is_overflow = True

        if is_overflow:
            overflow_events.extend(day_events)
            for remaining_day in grouped_events_iter:
                overflow_events.extend(remaining_day)
            break

        # Prepare header and event elements for the day
        day_header_str = f'<text x="{x_px}" y="{int(y_px)}" font-size="25px" font-weight="bold">{day.strftime("%A, %d %B")}</text>'
        y_after_header = y_px + (y_increment_px * 1.2)
        
        day_event_elements = []
        day_overflow_events = []
        y_px_for_day = y_after_header

        for event_data in day_events:
            if not is_overflow and y_px_for_day + y_increment_px > svg_height - bottom_margin:
                is_overflow = True
            
            if is_overflow:
                day_overflow_events.append(event_data)
                continue

            summary = event_data['summary'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Treat timed events that span across midnight as all-day events for the partial days
            is_all_day_display = event_data.get('is_all_day', False) or event_data.get('is_partial_span', False)

            if is_all_day_display:
                entry_name = "All-day: " + summary
                day_event_elements.append(f'<text x="{x_px}" y="{int(y_px_for_day)}" font-size="17" font-weight="bold">{entry_name}</text>')
            else:
                dtstart_nz = event_data['dtstart_nz']
                dtend_nz = event_data['dtend_nz']
                entry_date = dtstart_nz.strftime("%H:%M") + '-' +  dtend_nz.strftime("%H:%M")

                day_event_elements.append(f'<text x="{x_px}" y="{int(y_px_for_day)}" font-size="17">{entry_date}</text>')
                day_event_elements.append(f'<text x="{x_px + x_name_offset}" y="{int(y_px_for_day)}" font-size="17">{summary}</text>')
            
            y_px_for_day += y_increment_px

        if day_event_elements:
            # Only add header if there are events to show for that day
            svg_elements.append(day_header_str)
            svg_elements.extend(day_event_elements)
            y_px = y_px_for_day
            y_px += y_increment_px / 2 # Add some space between days
        else:
            # No events for this day fit, so the whole day becomes overflow
            is_overflow = True
            overflow_events.extend(day_events)
            for remaining_day in grouped_events_iter:
                overflow_events.extend(remaining_day)
            break

        if day_overflow_events:
            overflow_events.extend(day_overflow_events)
            for remaining_day in grouped_events_iter:
                overflow_events.extend(remaining_day)
            break

    # Construct the final SVG
    output = '<svg width="600" height="800" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">'
    output += '\n'.join(svg_elements)
    output += '\n</svg>'

    codecs.open(filename, 'w', encoding='utf-8').write(output)
    
    return overflow_events


# --- Main script ---

urllib.request.urlretrieve(ICAL_URL, "basic.ics")

ical_content = open('basic.ics', 'rb').read()
ical_calendar = Calendar.from_ical(ical_content)

# Fetch events for a longer period (e.g., 31 days) to have enough for multiple pages
today = datetime.date.today()
fourteen_days_out = today + timedelta(days=31)
nz_tz = zoneinfo.ZoneInfo("Pacific/Auckland")
utc_tz = zoneinfo.ZoneInfo("UTC")

# Get all events in the range
event_list = recurring_ical_events.of(ical_calendar).between(
    today,
    fourteen_days_out
)

all_events = []
for component in event_list:
    summary = str(component.get('summary'))
    dtstart = component.get('dtstart').dt
    dtend = component.get('dtend').dt
    is_all_day = not isinstance(dtstart, datetime.datetime)

    if is_all_day:
        # All-day event. dtstart and dtend are date objects. The end date is exclusive.
        start_date = dtstart
        end_date = dtend
        
        current_date = start_date
        while current_date < end_date:
            # Only add event instances that fall within our desired window
            if today <= current_date < fourteen_days_out:
                all_events.append({
                    'summary': summary,
                    'is_all_day': True,
                    'start_date': current_date,
                    'end_date_exclusive': end_date,
                    'sort_key': datetime.datetime.combine(current_date, datetime.time.min),
                })
            current_date += timedelta(days=1)
    else:
        # Timed event
        if dtstart.tzinfo is None: dtstart = dtstart.replace(tzinfo=utc_tz)
        dtstart_nz = dtstart.astimezone(nz_tz)

        if dtend.tzinfo is None: dtend = dtend.replace(tzinfo=utc_tz)
        dtend_nz = dtend.astimezone(nz_tz)

        current_date = dtstart_nz.date()
        end_date = dtend_nz.date()

        while current_date <= end_date:
            # Handle events ending exactly at midnight; they don't occur on the next day.
            if current_date == end_date and dtend_nz.time() == datetime.time(0, 0) and dtstart_nz.date() != dtend_nz.date():
                break

            # Only add event instances that fall within our desired window
            if today <= current_date < fourteen_days_out:
                 # Flag timed events that span multiple days to display them as all-day
                 is_partial_span = (dtstart_nz.date() < current_date) or (dtend_nz.date() > current_date)
                 all_events.append({
                    'summary': summary,
                    'is_all_day': False,
                    'is_partial_span': is_partial_span,
                    'start_date': current_date,       # The day this instance of the event is on
                    'sort_key': dtstart_nz,           # Sort all instances by the original start time
                    'dtstart_nz': dtstart_nz,         # The original start time (for display)
                    'dtend_nz': dtend_nz,             # The original end time (for display)
                })
            current_date += timedelta(days=1)

# Sort all events: first by date, then all-day events first, then by time
all_events.sort(key=lambda e: (e['start_date'], not e['is_all_day'], e['sort_key']))

# --- Filter out events that ended more than 4 hours ago ---
now_in_nz = datetime.datetime.now(nz_tz)
four_hours_ago = now_in_nz - timedelta(hours=4)

filtered_events = []
for event in all_events:
    if event['is_all_day']:
        # For all-day events, check their original end date.
        if event['end_date_exclusive'] < today:
            continue
        else:
            filtered_events.append(event)
    else:
        # For timed events, check their original end time.
        event_end_time = event['dtend_nz']
        if event_end_time < four_hours_ago:
            continue
        else:
            filtered_events.append(event)

# Generate first page and get overflow events
overflow_events = generate_svg_for_page(filtered_events, 'almost_done_0.svg')

# Generate second page with overflow events
generate_svg_for_page(overflow_events, 'almost_done_1.svg')
