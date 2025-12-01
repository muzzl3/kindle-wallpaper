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

urllib.request.urlretrieve(ICAL_URL, "basic.ics")

ical_content = open('basic.ics', 'rb').read()
ical_calendar = Calendar.from_ical(ical_content)

# --- New logic to group events by day ---

events = []
today = datetime.date.today()
seven_days_out = today + timedelta(days=7)
nz_tz = zoneinfo.ZoneInfo("Pacific/Auckland")
utc_tz = zoneinfo.ZoneInfo("UTC")

# Get all events in the range, including recurring ones, using the correct API
event_list = recurring_ical_events.of(ical_calendar).between(
    today,
    seven_days_out
)

for component in event_list:
    dtstart = component.get('dtstart').dt
    is_all_day = not isinstance(dtstart, datetime.datetime)

    if is_all_day:
        # All-day events have no timezone
        start_date = dtstart
        sort_key = datetime.datetime.combine(start_date, datetime.time.min)
        events.append({
            'summary': str(component.get('summary')),
            'is_all_day': True,
            'start_date': start_date,
            'sort_key': sort_key,
        })
    else:
        # It's a datetime object, handle timezone conversion
        dtend = component.get('dtend').dt

        # Make aware (assume UTC if naive) and convert to NZ time
        if dtstart.tzinfo is None:
            dtstart = dtstart.replace(tzinfo=utc_tz)
        dtstart_nz = dtstart.astimezone(nz_tz)

        if dtend.tzinfo is None:
            dtend = dtend.replace(tzinfo=utc_tz)
        dtend_nz = dtend.astimezone(nz_tz)

        start_date = dtstart_nz.date()
        sort_key = dtstart_nz

        events.append({
            'summary': str(component.get('summary')),
            'is_all_day': False,
            'start_date': start_date,
            'sort_key': sort_key,
            'dtstart_nz': dtstart_nz,
            'dtend_nz': dtend_nz,
        })

# Sort events: first by date, then all-day events first, then by time
events.sort(key=lambda e: (e['start_date'], not e['is_all_day'], e['sort_key']))


# --- Dynamically calculate spacing to fill height ---

# Group events by day to count them
# The groupby iterator can only be consumed once, so we store the groups
grouped_events = [list(g) for k, g in groupby(events, key=lambda e: e['start_date'])]
num_days = len(grouped_events)
num_events = len(events)

# Define available height and margins
svg_height = 800
top_margin = 50
bottom_margin = 20 # Buffer at the bottom
available_height = svg_height - top_margin - bottom_margin

# Calculate the ideal line height increment
y_increment_px = 40  # Default value
if num_days > 0 or num_events > 0:
    # A day header takes up 1.2 units, and the space after a day takes 0.5 units. An event takes 1 unit.
    total_units = (num_days * 1.2) + num_events + (num_days * 0.5)
    if total_units > 0:
        calculated_increment = available_height / total_units
        # Ensure the increment is not so small that text overlaps
        # Header font is 25, event font is 17.
        # Header line height is 1.2 * increment, must be > 25, so increment > 20.83
        # Event line height is increment, must be > 17.
        min_increment = 21
        y_increment_px = max(calculated_increment, min_increment)


# --- Generate a blank SVG with calendar elements grouped by day ---

svg_elements = []
y_px = float(top_margin)
x_px = 20
x_name_offset = 260 # x for the name part of normal events

# Use the pre-grouped events
for day_events in grouped_events:
    if not day_events:
        continue
    day = day_events[0]['start_date']

    # Add a header for the day
    # Use int(y_px) for pixel values as SVG attributes must be integers
    svg_elements.append(f'<text x="{x_px}" y="{int(y_px)}" font-size="25px" font-weight="bold">{day.strftime("%A, %d %B")}</text>')
    y_px += y_increment_px * 1.2

    for event_data in day_events:
        summary = event_data['summary'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        if event_data['is_all_day']:
            entry_name = "All-day: " + summary
            svg_elements.append(f'<text x="{x_px}" y="{int(y_px)}" font-size="17" font-weight="bold">{entry_name}</text>')
        else:
            dtstart_nz = event_data['dtstart_nz']
            dtend_nz = event_data['dtend_nz']
            entry_date = dtstart_nz.strftime("%H:%M") + '-' +  dtend_nz.strftime("%H:%M")

            svg_elements.append(f'<text x="{x_px}" y="{int(y_px)}" font-size="17">{entry_date}</text>')
            svg_elements.append(f'<text x="{x_px + x_name_offset}" y="{int(y_px)}" font-size="17">{summary}</text>')
        
        y_px += y_increment_px
    
    y_px += y_increment_px / 2 # Add some space between days


# Construct the final SVG
output = '<svg width="600" height="800" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans">\n'
output += '\n'.join(svg_elements)
output += '\n</svg>'

# Write output
codecs.open('almost_done.svg', 'w', encoding='utf-8').write(output)