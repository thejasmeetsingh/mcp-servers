import os
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from httpx import AsyncClient, HTTPStatusError, TimeoutException

from utils import convert_dict_to_markdown, format_weather_data


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
MAX_REQUEST_TIMEOUT = 30  # seconds
DEFAULT_SEARCH_RADIUS = 500.0  # meters
MAX_SEARCH_RADIUS = 50000.0  # meters
DEFAULT_FORECAST_DAYS = 7
MAX_FORECAST_DAYS = 14
MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0
MIN_RADIUS = 0.0
MIN_DAYS = 1

# API Endpoints
GEOCODING_ENDPOINT = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
ROUTES_ENDPOINT = "https://routes.googleapis.com/directions/v2:computeRoutes"
WEATHER_ENDPOINT = "https://weather.googleapis.com/v1/forecast/days:lookup"
AIR_QUALITY_ENDPOINT = "https://airquality.googleapis.com/v1/forecast:lookup"


class Config:
    """Configuration class for API settings."""

    def __init__(self):
        """Initialize configuration with environment variables."""

        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY environment variable is required")


class TravelMode(Enum):
    """Enumeration of supported travel modes for routing."""

    DRIVE = "DRIVE"
    BICYCLE = "BICYCLE"
    WALK = "WALK"
    TWO_WHEELER = "TWO_WHEELER"
    TRANSIT = "TRANSIT"


class TransitMode(Enum):
    """Enumeration of supported transit modes."""

    BUS = "BUS"
    RAIL = "RAIL"


class RankPreference(Enum):
    """Enumeration of supported ranking preferences for place searches."""

    RELEVANCE = "RELEVANCE"
    DISTANCE = "DISTANCE"


@dataclass
class Location:
    """Data class representing geographical coordinates."""

    latitude: float
    longitude: float

    def to_dict(self) -> Dict[str, float]:
        """Convert location to dictionary format."""

        return {"latitude": self.latitude, "longitude": self.longitude}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Location':
        """Create Location instance from dictionary."""

        return cls(latitude=data["latitude"], longitude=data["longitude"])


class GoogleMapsAPIError(Exception):
    """Custom exception for Google Maps API related errors."""


# Initialize configuration and MCP server
config = Config()
mcp = FastMCP("google-maps")


async def make_api_request(
    client: AsyncClient,
    method: str,
    url: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Make an API request with proper error handling.

    Args:
        client: HTTP client instance
        method: HTTP method ('GET' or 'POST')
        url: Request URL
        **kwargs: Additional request parameters

    Returns:
        JSON response as dictionary

    Raises:
        GoogleMapsAPIError: For API-related errors
        TimeoutException: For request timeouts
    """

    try:
        if method.upper() == 'GET':
            response = await client.get(url, **kwargs)
        elif method.upper() == 'POST':
            response = await client.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    except HTTPStatusError as exc:
        logger.error("HTTP error %d: %s", exc.response.status_code,
                     exc.response.text)
        raise GoogleMapsAPIError(
            f"API request failed: {exc.response.status_code}"
        ) from exc
    except TimeoutException as exc:
        logger.error("Request timeout after %d seconds", MAX_REQUEST_TIMEOUT)
        raise GoogleMapsAPIError("Request timed out") from exc
    except Exception as exc:
        logger.error("Unexpected error during API request: %s", str(exc))
        raise GoogleMapsAPIError(f"Unexpected error: {str(exc)}") from exc


def validate_coordinates(location: Dict[str, float]) -> None:
    """
    Validate latitude and longitude coordinates.

    Args:
        location: Dictionary containing latitude and longitude

    Raises:
        ValueError: If coordinates are invalid
    """

    lat = location.get("latitude")
    lng = location.get("longitude")
    error = None

    if lat is None or lng is None:
        error = "Location must contain both 'latitude' and 'longitude'"

    if not (MIN_LATITUDE <= lat <= MAX_LATITUDE):
        error = f"Latitude must be between {MIN_LATITUDE} and {MAX_LATITUDE}"

    if not (MIN_LONGITUDE <= lng <= MAX_LONGITUDE):
        error = f"Longitude must be between {MIN_LONGITUDE} and {MAX_LONGITUDE}"

    if error:
        raise ValueError(error)


def validate_radius(radius: float) -> None:
    """
    Validate search radius.

    Args:
        radius: Search radius in meters

    Raises:
        ValueError: If radius is invalid
    """

    if not (MIN_RADIUS <= radius <= MAX_SEARCH_RADIUS):
        raise ValueError(f"Radius must be between {MIN_RADIUS} and "
                         f"{MAX_SEARCH_RADIUS}, got {radius}")


def validate_non_empty_string(value: str, field_name: str) -> None:
    """
    Validate that a string is not empty or whitespace only.

    Args:
        value: String value to validate
        field_name: Name of the field for error messages

    Raises:
        ValueError: If string is empty or whitespace only
    """

    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def validate_enum_value(value: str, enum_class: type, field_name: str) -> None:
    """
    Validate that a value is a valid enum member.

    Args:
        value: Value to validate
        enum_class: Enum class to check against
        field_name: Name of the field for error messages

    Raises:
        ValueError: If value is not a valid enum member
    """

    valid_values = [e.value for e in enum_class]
    if value not in valid_values:
        raise ValueError(f"{field_name} must be one of: {valid_values}")


def get_geocoding_params(address: str) -> Dict[str, str]:
    """Get parameters for geocoding API request."""

    return {"address": address.strip(), "key": config.api_key}


def get_places_headers() -> Dict[str, str]:
    """Get headers for places API request."""

    fields = [
        "places.id",
        "places.internationalPhoneNumber",
        "places.formattedAddress",
        "places.location",
        "places.rating",
        "places.googleMapsUri",
        "places.businessStatus",
        "places.displayName",
        "places.websiteUri",
        "places.priceLevel",
        "places.userRatingCount"
    ]

    return {
        "X-Goog-FieldMask": ",".join(fields),
        "X-Goog-Api-Key": config.api_key,
        "Content-Type": "application/json"
    }


def get_routes_headers() -> Dict[str, str]:
    """Get headers for routes API request."""

    fields = [
        "routes.routeLabels",
        "routes.distanceMeters",
        "routes.duration",
        "routes.description",
        "routes.warnings",
        "routes.travelAdvisory",
        "routes.legs.distanceMeters",
        "routes.legs.duration",
        "routes.legs.steps.distanceMeters",
        "routes.legs.steps.staticDuration",
        "routes.legs.steps.navigationInstruction",
        "routes.legs.steps.travelMode",
        "routes.polyline"
    ]

    return {
        "X-Goog-FieldMask": ",".join(fields),
        "X-Goog-Api-Key": config.api_key,
        "Content-Type": "application/json"
    }


def get_weather_fields() -> List[str]:
    """Get field list for weather API request."""

    return [
        "timeZone",
        "forecastDays.interval",
        "forecastDays.daytimeForecast.weatherCondition.description",
        "forecastDays.nighttimeForecast.weatherCondition.description",
        "forecastDays.maxTemperature",
        "forecastDays.minTemperature",
    ]


def get_air_quality_fields() -> List[str]:
    """Get field list for air quality API request."""

    return [
        "nextPageToken",
        "hourlyForecasts.dateTime",
        "hourlyForecasts.indexes.aqi",
        "hourlyForecasts.indexes.category",
        "hourlyForecasts.indexes.dominantPollutant",
        "hourlyForecasts.healthRecommendations"
    ]


@mcp.tool()
async def address_geocoding(address: str) -> str:
    """
    Convert a street address to geographic coordinates (latitude/longitude).

    This function uses the Google Maps Geocoding API to transform
    human-readable addresses into precise geographic coordinates.

    Args:
        address: Street address to geocode

    Returns:
        Markdown-formatted string containing coordinates

    Raises:
        ValueError: If address is empty or no coordinates found
        GoogleMapsAPIError: If API request fails
    """

    validate_non_empty_string(address, "Address")

    params = get_geocoding_params(address)

    async with AsyncClient(timeout=MAX_REQUEST_TIMEOUT) as client:
        data = await make_api_request(client, "GET", GEOCODING_ENDPOINT,
                                      params=params)

    results = data.get("results", [])
    if not results:
        raise ValueError(
            f"No coordinates found for address: '{address}'. "
            "Please verify the address is correct and try again."
        )

    location = results[0]["geometry"]["location"]
    logger.info("Successfully geocoded address: %s", address)

    return convert_dict_to_markdown(location)


@mcp.tool()
async def search_places(
    query: str,
    location: Dict[str, float],
    radius: float = DEFAULT_SEARCH_RADIUS,
    order_by: Optional[str] = None
) -> str:
    """
    Search for places near a specific location based on a text query.

    Args:
        query: Search term or query string
        location: Geographic coordinates as a dictionary
        radius: Search radius in meters (0.0 to 50,000.0)
        order_by: Result ranking preference ("RELEVANCE" or "DISTANCE")

    Returns:
        Markdown-formatted string containing place information

    Raises:
        ValueError: If inputs are invalid
        GoogleMapsAPIError: If API request fails
    """

    # Input validation
    validate_non_empty_string(query, "Search query")
    validate_coordinates(location)
    validate_radius(radius)

    if order_by is not None:
        validate_enum_value(order_by, RankPreference, "order_by")

    headers = get_places_headers()

    payload = {
        "textQuery": query.strip(),
        "locationBias": {
            "circle": {
                "center": location,
                "radius": radius
            }
        },
        "pageSize": 10,
    }

    if order_by:
        payload["rankPreference"] = order_by

    async with AsyncClient(timeout=MAX_REQUEST_TIMEOUT) as client:
        data = await make_api_request(client, "POST", PLACES_ENDPOINT,
                                      headers=headers, json=payload)

    places = data.get("places", [])
    if not places:
        return (
            f"No places found for query '{query}' within {radius}m radius. "
            "Try expanding your search radius or using different keywords."
        )

    logger.info("Found %d places for query: %s", len(places), query)
    return convert_dict_to_markdown({"places": places})


@mcp.tool()
async def get_route(
    source: str,
    destination: str,
    travel_mode: str,
    transit_travel_mode: str = TransitMode.RAIL.value
) -> str:
    """
    Calculate route directions between two locations with traffic data.

    Args:
        source: Starting location address or plus code
        destination: Ending location address or plus code
        travel_mode: Transportation method
        transit_travel_mode: Public transit preference

    Returns:
        Markdown-formatted string containing route information

    Raises:
        ValueError: If addresses are empty or travel mode is invalid
        GoogleMapsAPIError: If API request fails or no routes found
    """

    # Input validation
    validate_non_empty_string(source, "Source address")
    validate_non_empty_string(destination, "Destination address")
    validate_enum_value(travel_mode, TravelMode, "travel_mode")
    validate_enum_value(transit_travel_mode, TransitMode,
                        "transit_travel_mode")

    headers = get_routes_headers()

    payload = {
        "origin": {"address": source.strip()},
        "destination": {"address": destination.strip()},
        "travelMode": travel_mode,
        "computeAlternativeRoutes": True,
        "routeModifiers": {
            "avoidTolls": False,
            "avoidHighways": False,
            "avoidFerries": False
        }
    }

    # Add transit preferences for public transport
    if travel_mode == TravelMode.TRANSIT.value:
        payload["transitPreferences"] = {
            "allowedTravelModes": [transit_travel_mode]
        }

    async with AsyncClient(timeout=MAX_REQUEST_TIMEOUT) as client:
        data = await make_api_request(client, "POST", ROUTES_ENDPOINT,
                                      headers=headers, json=payload)

    routes = data.get("routes", [])
    if not routes:
        raise GoogleMapsAPIError(
            f"No routes found between '{source}' and '{destination}' "
            f"for travel mode '{travel_mode}'. Please verify the addresses."
        )

    logger.info("Found %d route(s) from %s to %s", len(routes),
                source, destination)

    return convert_dict_to_markdown({"routes": routes})


@mcp.tool()
async def get_weather_forecast(
    location: Dict[str, float],
    days: int = DEFAULT_FORECAST_DAYS
) -> str:
    """
    Retrieve detailed weather forecast for a specific location.

    Args:
        location: Geographic coordinates
        days: Number of forecast days (1-14)

    Returns:
        Markdown-formatted string containing weather forecast

    Raises:
        ValueError: If location coordinates are invalid or days out of range
        GoogleMapsAPIError: If API request fails or no forecast available
    """

    # Input validation
    validate_coordinates(location)

    if not (MIN_DAYS <= days <= MAX_FORECAST_DAYS):
        raise ValueError(f"Days must be between {MIN_DAYS} and "
                         f"{MAX_FORECAST_DAYS}, got {days}")

    fields = get_weather_fields()

    params = {
        "key": config.api_key,
        "location.latitude": location["latitude"],
        "location.longitude": location["longitude"],
        "days": days,
        "pageSize": 10,
        "fields": ",".join(fields),
    }

    async with AsyncClient(timeout=MAX_REQUEST_TIMEOUT) as client:
        data = await make_api_request(client, "GET", WEATHER_ENDPOINT,
                                      params=params)

    forecast = data.get("forecastDays", [])
    if not forecast:
        raise GoogleMapsAPIError(
            f"No weather forecast available for location "
            f"({location['latitude']}, {location['longitude']})"
        )

    timezone = data.get("timeZone", {}).get("id", "Unknown")

    logger.info("Retrieved %d-day weather forecast", len(forecast))

    return convert_dict_to_markdown({
        "forecast": format_weather_data(forecast),
        "timezone": timezone
    })


@mcp.tool()
async def get_air_quality_forecast(
    location: Dict[str, float],
    interval: Dict[str, str],
    page_token: str = ""
) -> str:
    """
    Retrieve air quality forecast and health recommendations.

    Args:
        location: Geographic coordinates
        interval: Time range for forecast
        page_token: Pagination token for additional results

    Returns:
        Markdown-formatted string containing air quality data

    Raises:
        ValueError: If location coordinates or time interval are invalid
        GoogleMapsAPIError: If API request fails or no data available
    """

    # Input validation
    validate_coordinates(location)

    required_interval_keys = {"startTime", "endTime"}
    if not all(key in interval for key in required_interval_keys):
        raise ValueError(
            f"Interval must contain {required_interval_keys}, "
            f"got {set(interval.keys())}"
        )

    # Validate timestamp format (basic check)
    for key, timestamp in interval.items():
        if not isinstance(timestamp, str) or len(timestamp) < 19:
            raise ValueError(f"Invalid timestamp format for {key}: "
                             f"{timestamp}")

    fields = get_air_quality_fields()

    payload = {
        "location": location,
        "period": interval,
        "pageToken": page_token
    }

    params = {
        "key": config.api_key,
        "fields": ",".join(fields)
    }

    async with AsyncClient(timeout=MAX_REQUEST_TIMEOUT) as client:
        data = await make_api_request(client, "POST", AIR_QUALITY_ENDPOINT,
                                      params=params, json=payload)

    forecast = data.get("hourlyForecasts", [])
    if not forecast:
        raise GoogleMapsAPIError(
            f"No air quality forecast available for location "
            f"({location['latitude']}, {location['longitude']}) "
            f"in the specified time interval"
        )

    next_page_token = data.get("nextPageToken", "")

    logger.info("Retrieved air quality forecast with %d hourly entries",
                len(forecast))

    return convert_dict_to_markdown({
        "forecast": forecast,
        "next_page_token": next_page_token
    })
