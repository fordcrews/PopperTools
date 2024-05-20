import requests
import datetime
import json
import subprocess
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Function to get current date and time
def get_date_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

# Function to get current temperature (example using OpenWeatherMap API)
def get_temperature(api_key, location):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    temp = data['main']['temp']
    return f"{temp}°C"

# Function to get today's events from Google Calendar
def get_calendar_events(credentials_file, calendar_id):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=["https://www.googleapis.com/auth/calendar.readonly"])
    service = build('calendar', 'v3', credentials=credentials)

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    end_of_day = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + 'Z'
    
    events_result = service.events().list(calendarId=calendar_id, timeMin=now, timeMax=end_of_day,
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    event_str = "Events: " + "; ".join([event['summary'] for event in events])
    return event_str

def send_to_doflinx(message, doflinx_path, device_number):
    cmd = f'"{doflinx_path}" {device_number} "{message}"'
    subprocess.run(cmd, shell=True)

# Replace with your actual values
API_KEY = "your_openweathermap_api_key"
LOCATION = "your_city"
GOOGLE_CREDENTIALS_FILE = "path_to_your_google_service_account_credentials.json"
CALENDAR_ID = "your_calendar_id"
DOFLINX_PATH = "C:\\DirectOutput\\DOFLinxMsg.exe"  # Update this path to your actual DOFLinxMsg.exe path
DEVICE_NUMBER = "1"  # Replace with the correct device number for your LED matrix

date_time = get_date_time()
temperature = get_temperature(API_KEY, LOCATION)
events = get_calendar_events(GOOGLE_CREDENTIALS_FILE, CALENDAR_ID)

message = f"Date: {date_time} Temp: {temperature} {events}"

print(message)
send_to_doflinx(message, DOFLINX_PATH, DEVICE_NUMBER)
