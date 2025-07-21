from typing import Any
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP, Context

from google_calender import Calendar
from utils import convert_dict_to_markdown


CREDENTIALS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
SKIPPABLE_ITEMS = {
    "kind",
    "etag",
    "htmlLink",
    "created",
    "updated",
    "creator",
    "organizer",
    "iCalUID",
    "eventType",
}


@asynccontextmanager
async def lifespan(_: FastMCP):
    """
    Initialize calendar instance which will be used by all the tools.
    """

    try:
        calendar = Calendar(
            credentials_filename=CREDENTIALS_FILE,
            scopes=SCOPES
        )

        yield calendar
    except Exception as e:
        print(e)
        raise ValueError(str(e)) from e


mcp = FastMCP("calendar", lifespan=lifespan)


@mcp.tool(
    name="Get Events",
    title="Get Calendar Events",
    annotations={"readOnlyHint": True}
)
def get_events(ctx: Context, max_results: int = 10) -> str:
    """
    Retrieve upcoming events from the user's calendar.

    Args:
        max_results (int, optional): Maximum number of events to return (default: 10)
    """

    try:
        calendar: Calendar = ctx.request_context.lifespan_context
        results = calendar.get_events(max_results=max_results)

        return convert_dict_to_markdown(
            {"results": results},
            skippable_items=SKIPPABLE_ITEMS
        ) if results else "No events found in the calendar."

    except Exception as e:
        raise ValueError(
            f"Error caught while fetching events from calendar: {str(e)}") from e


@mcp.tool(
    name="Search Event",
    title="Search Calendar Events",
    annotations={"readOnlyHint": True}
)
def search_event(ctx: Context, query: str, max_results: int = 10) -> str:
    """
    Search for events matching a specific query in the calendar.

    Args:
        query (str): Search query string (e.g., event title or keyword)
        max_results (int, optional): Maximum number of events to return (default: 10)
    """

    try:
        calendar: Calendar = ctx.request_context.lifespan_context
        results = calendar.search_event(query, max_results=max_results)

        return convert_dict_to_markdown(
            {"results": results},
            skippable_items=SKIPPABLE_ITEMS
        ) if results else "No events found in the calendar for the given query."

    except Exception as e:
        raise ValueError(
            f"Error caught while searching an event: {str(e)}") from e


@mcp.tool(
    name="Add Event",
    title="Add a Calendar Event",
    annotations={"readOnlyHint": True}
)
def add_event(
    ctx: Context,
    summary: str,
    start_time: str,
    end_time: str,
    description: str | None = None,
    location: str | None = None,
    reminders: list[dict[str, Any]] | None = None,
    attendees: list[dict[str, Any]] | None = None,
    time_zone: str = "UTC"
) -> str:
    """
    Create a new event with full details including time, reminders, attendees, and more.

    Args:
        summary (str): Event title
        start_time: (str): Start time in RFC3339 format (e.g., '2025-05-16T10:00:00')
        end_time (str): End time in RFC3339 format
        description (str, optional): Optional description of the event
        location (str, optional): location string (e.g., New York, Mumbai etc)
        reminders (list, optional): list of reminders (e.g., [{'method': 'popup', 'minutes': 10}])
        attendees (list, optional): list of attendees (e.g., [{'email': 'person@example.com'}])
        time_zone (str, optional): Time zone string (default: 'UTC')
    """

    try:
        calendar: Calendar = ctx.request_context.lifespan_context
        result = calendar.insert_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            reminders=reminders,
            attendees=attendees,
            time_zone=time_zone
        )

        return convert_dict_to_markdown(result, skippable_items=SKIPPABLE_ITEMS)

    except Exception as e:
        raise ValueError(
            f"Error caught while adding an event: {str(e)}") from e


@mcp.tool(
    name="Get Event Detail",
    title="Get a Calendar Event Details",
    annotations={"readOnlyHint": True}
)
def get_event_detail(
    ctx: Context,
    event_id: str,
    time_zone: str = "UTC"
) -> str:
    """
    Retrieve an event details from the calendar.

    Args:
        event_id (str): ID of the event to delete
        time_zone (str, optional): Time zone string (default: 'UTC')
    """

    try:
        calendar: Calendar = ctx.request_context.lifespan_context
        result = calendar.get_event_detail(
            event_id=event_id,
            time_zone=time_zone
        )
        return convert_dict_to_markdown(result, skippable_items=SKIPPABLE_ITEMS)

    except Exception as e:
        raise ValueError(
            f"Error caught while retrieving an event: {str(e)}") from e


@mcp.tool(
    name="Update Event",
    title="Update a Calendar Event Details",
    annotations={"readOnlyHint": True}
)
def update_event(
    ctx: Context,
    event_id: str,
    updated_fields: dict[str, Any],
) -> str:
    """
    Update an existing event with new fields.

    Args
        event_id (str): ID of the event to update
        updated_fields (dict): Dictionary of fields to update
                                (e.g., {"summary": "New Title", "description": "New Description"})
    """

    try:
        calendar: Calendar = ctx.request_context.lifespan_context
        result = calendar.update_event(
            event_id=event_id,
            updated_fields=updated_fields,
        )

        return convert_dict_to_markdown(result, skippable_items=SKIPPABLE_ITEMS)

    except Exception as e:
        raise ValueError(
            f"Error caught while updating an event: {str(e)}") from e


@mcp.tool(
    name="Delete Event",
    title="Delete a Calendar Event",
    annotations={"readOnlyHint": True}
)
def delete_event(
    ctx: Context,
    event_id: str,
) -> str:
    """
    Delete an event from the calendar.

    Args:
        event_id (str): ID of the event to delete
    """

    try:
        calendar: Calendar = ctx.request_context.lifespan_context
        result = calendar.delete_event(event_id=event_id)
        return result

    except Exception as e:
        raise ValueError(
            f"Error caught while deleting an event: {str(e)}") from e
