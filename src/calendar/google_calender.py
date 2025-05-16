from datetime import datetime, UTC
from typing import Any

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


class Calendar:
    """
    A wrapper class for interacting with Google Calendar using an authorized credentials object.
    Provides methods to list, search, insert, update, and delete calendar events.
    """

    def __init__(self, credentials_filename: str, scopes: list[str]):
        """
        Initialize the Calendar object with the provided OAuth 2.0 credentials and scopes.

        Args:
            credentials_filename (str): Credentials filename which contains user auth tokens.
            scopes (list): Google Calendar API scopes.
        """

        google_credentials = Credentials.from_authorized_user_file(
            credentials_filename,
            scopes=scopes
        )

        refresh_credentials = (
            not google_credentials.valid and
            google_credentials.expired and
            google_credentials.refresh_token
        )

        if refresh_credentials:
            google_credentials.refresh(Request())

        self.service = build("calendar", "v3", credentials=google_credentials)

    def get_events(
        self,
        calendar_id: str = "primary",
        max_results: int = 10
    ) -> list[dict[str, Any]]:

        # Current time in RFC3339 format
        now = datetime.now(tz=UTC).isoformat()

        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])

    def search_event(
        self,
        query: str,
        calendar_id: str = "primary",
        max_results: int = 10
    ) -> list[dict[str, Any]]:

        events_result = self.service.events().list(
            calendarId=calendar_id,
            q=query,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])

    def insert_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        calendar_id: str = "primary",
        description: str | None = None,
        location: str | None = None,
        reminders: list[dict[str, Any]] | None = None,
        attendees: list[dict[str, Any]] | None = None,
        time_zone: str = "UTC"
    ) -> dict[str, Any]:

        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time,
                "timeZone": time_zone
            },
            "end": {
                "dateTime": end_time,
                "timeZone": time_zone
            },
            "reminders": {
                "useDefault": False,
                "overrides": reminders or []
            },
            "attendees": attendees or []
        }

        # Call Google Calendar API to insert the event
        created_event = self.service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

        return created_event

    def get_event_detail(
        self,
        event_id: str,
        calendar_id: str = "primary",
        time_zone: str = "UTC"
    ) -> str:

        event = self.service.events().get(
            calendarId=calendar_id,
            eventId=event_id,
            timeZone=time_zone,
        ).execute()

        return event

    def update_event(
        self,
        event_id: str,
        updated_fields: dict[str, Any],
        calendar_id: str = "primary"
    ) -> dict[str, Any]:

        # Fetch the existing event
        event = self.service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        # Apply the updates
        event.update(updated_fields)

        # Send the update request
        updated_event = self.service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()

        return updated_event

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> str:

        self.service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        return f"Event {event_id} deleted successfully."
