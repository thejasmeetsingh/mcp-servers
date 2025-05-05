import os
from contextlib import asynccontextmanager

from httpx import AsyncClient
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

from schema import (
    GenreResponse,
    GenreListResponse,
    PlatformResponse,
    PlatformListResponse,
    GameResponse,
    GameListResponse,
    GameScreenshotResponse,
    GameScreenshotListResponse,
    GameTrailerResponse,
    GameTrailerListResponse,
    GameDetailResponse
)


# Load env variables located in .env file
load_dotenv()
BASE_URL = os.getenv("RAWG_API_BASE_URL")
API_KEY = os.getenv("RAWG_API_KEY")
RAWG_RESULT_PAGE_SIZE = 10


@asynccontextmanager
async def lifespan(server: FastMCP):
    """
    Initialize an async httpx client which will part of the request content.
    And it'll be used in all the methods for fetching data from RAWG API service
    """

    if not BASE_URL or not API_KEY:
        raise ValueError("RAWG API service credentials are not configured in the enviorment." \
        "Please check your enviorment varriables and try again.")

    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "rawg-db-mcp/1.0"
        }

        default_params = {
            "key": API_KEY,
            "page_size": RAWG_RESULT_PAGE_SIZE
        }

        async with AsyncClient(base_url=BASE_URL, headers=headers, params=default_params, timeout=30) as client:
            yield client
    except Exception as e:
        raise ValueError(f"Error caught while calling RAWG API service: {str(e)}")
    finally:
        await client.aclose()


# Create MCP server instance
mcp = FastMCP(name="rawg-db-mcp", lifespan=lifespan)


@mcp.resource(uri="/genres")
async def get_video_games_genre_list(ctx: Context, page: int = 1) -> GenreListResponse:
    """
    Get list of video game genres. Like: Action, Adventure, Indie etc

    Args:
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get("/genres", params={"page": page})
        response.raise_for_status()
        response = response.json()

        await ctx.report_progress(75, 100)

        return GenreListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GenreResponse(
                    id=item["id"],
                    name=item["name"],
                    games_count=item["games_count"],
                )
                for item in response.get("results", [])
            ]
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the genre list: {str(e)}")


@mcp.resource(uri="/genre-details")
async def get_video_game_genre_detail(ctx: Context, id: int) -> GenreResponse:
    """
    Get detail of a video game genres, Like its name, description and related image

    Args:
        id: An integer representing the genre ID
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get(f"/genres/{id}")
        response.raise_for_status()
        response = response.json()

        return GenreResponse(
            id=response["id"],
            name=response["name"],
            games_count=response["games_count"],
            description=response["description"],
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the genre detail: {str(e)}")


@mcp.resource(uri="/platforms")
async def get_video_game_platforms(ctx: Context, page: int = 1) -> PlatformListResponse:
    """
    Get list of a video game platforms, Like: PS4, PS2, Xbox, PC etc.

    Args:
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get("/platforms", params={"page": page})
        response.raise_for_status()
        response = response.json()

        return PlatformListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                PlatformResponse(
                    id=item["id"],
                    name=item["name"],
                    games_count=item["games_count"],
                    year_start=item.get("year_start"),
                    year_end=item.get("year_end")
                )
                for item in response.get("results", [])
            ]
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the platform list: {str(e)}")


@mcp.resource(uri="games/")
async def get_video_games_list(
    ctx: Context,
    page: int = 1,
    search: str | None = None,
    platforms: str | None = None,
    genres: str | None = None,
    dates: str | None = None,
    metacritic: str | None = None,
    ordering: str | None = None
) -> GameListResponse:
    """
    Get list of a video games.

    Args:
        page: An integer representing the page number that needs to be fetched from the service.
        search: An optional string which contains the search query.
        
        platforms: An optional comma-seperated string,
                    To perform filter on the games list by platform IDs. Like: 4,5 or 5.

        genres: An optional comma-seperated string,
                To perform filter on the games list by genre IDs or names. Like: 1,2 or 4 or action or action,indie.

        dates: An optional comma-seperated string,
                To perform filter on the games list by release date. Like: 2010-01-01,2018-12-31 or 2010-01-01
        
        metacritic: An optional comma-seperated string,
                        To perform filter on the games list by metacritic rating. Like: 80,100
        
        ordering: An optional string for performing ordering on the games list.
                    The string value should be the following fields names:
                    - name
                    - released
                    - created
                    - rating
                    - metacritic
                
                You can reverse the sort order by adding a hyphen, Like: -released
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        params = {"page": page, "exclude_stores": True, }

        # Update the query params based on if they actually contain some value.
        if search:
            params.update({"search": search})
        if platforms:
            params.update({"platforms": platforms})
        if genres:
            params.update({"genres": genres})
        if dates:
            params.update({"dates": dates})
        if metacritic:
            params.update({"metacritic": metacritic})
        if ordering:
            params.update({"ordering": metacritic})

        response = await client.get("/games", params=params)
        response.raise_for_status()
        response = response.json()

        return GameListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GameResponse(
                    id=item["id"],
                    name=item["name"],
                    released=item["released"],
                    rating=item["rating"],
                    rating_top=item["rating_top"],
                    ratings_count=item["ratings_count"],
                    ratings=item.get("ratings", []),
                    metacritic=item.get("metacritic"),
                    playtime=item["playtime"],
                    esrb_rating=item.get("esrb_rating"),
                    platforms=[
                        {
                            "id": platform["platform"]["id"],
                            "name": platform["platform"]["name"]
                        }
                        for platform in item.get("platforms", [])
                    ]
                )
                for item in response.get("results", [])
            ]
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the games list: {str(e)}")


@mcp.resource(uri="/additions")
async def get_video_game_additions(ctx: Context, game_id: int, page: int = 1) -> GameListResponse:
    """
    Get a list of additions or DLC's for the given game ID, GOTY and other editions, companion apps, etc.

    Args:
        game_id: An integer containing the ID of a game.
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get(f"/games/{game_id}/additions", params={"page": page})
        response.raise_for_status()
        response = response.json()

        return GameListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GameResponse(
                    id=item["id"],
                    name=item["name"],
                    released=item["released"],
                    rating=item["rating"],
                    rating_top=item["rating_top"],
                    ratings_count=item["ratings_count"],
                    ratings=item.get("ratings", []),
                    metacritic=item.get("metacritic"),
                    playtime=item["playtime"],
                    esrb_rating=item.get("esrb_rating"),
                    platforms=[
                        {
                            "id": platform["platform"]["id"],
                            "name": platform["platform"]["name"]
                        }
                        for platform in item.get("platforms", [])
                    ]
                )
                for item in response.get("results", [])
            ]
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the additions of a game: {str(e)}")


@mcp.resource(uri="/game-series")
async def get_video_game_series(ctx: Context, game_id: int, page: int = 1) -> GameListResponse:
    """
    Get a list of games that are part of the same series based on the given game ID.

    Args:
        game_id: An integer containing the ID of a game.
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get(f"/games/{game_id}/game-series", params={"page": page})
        response.raise_for_status()
        response = response.json()

        return GameListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GameResponse(
                    id=item["id"],
                    name=item["name"],
                    released=item["released"],
                    rating=item["rating"],
                    rating_top=item["rating_top"],
                    ratings_count=item["ratings_count"],
                    ratings=item.get("ratings", []),
                    metacritic=item.get("metacritic"),
                    playtime=item["playtime"],
                    esrb_rating=item.get("esrb_rating"),
                    platforms=[
                        {
                            "id": platform["platform"]["id"],
                            "name": platform["platform"]["name"]
                        }
                        for platform in item.get("platforms", [])
                    ]
                )
                for item in response.get("results", [])
            ]
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the series of a game: {str(e)}")


@mcp.resource(uri="/game-screenshots")
async def get_video_game_screenshots(ctx: Context, game_id: int, page: int = 1) -> GameScreenshotListResponse:
    """
    Get screenshots or images for the given game ID.

    Args:
        game_id: An integer containing the ID of a game.
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get(f"/games/{game_id}/screenshots", params={"page": page})
        response.raise_for_status()
        response = response.json()

        return GameScreenshotListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GameScreenshotResponse(
                    id=item["id"],
                    image=item["image"],
                    width=item["width"],
                    height=item["height"]
                )
                for item in response.get("results", [])
            ]
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the screenshots of a game: {str(e)}")


@mcp.resource(uri="/game-trailers")
async def get_video_game_trailers(ctx: Context, game_id: int, page: int = 1) -> GameTrailerListResponse:
    """
    Get a list of trailers/movies/gameplays etc of a given game ID.

    Args:
        game_id: An integer containing the ID of a game.
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get(f"/games/{game_id}/movies", params={"page": page})
        response.raise_for_status()
        response = response.json()

        return GameTrailerListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GameTrailerResponse(
                    id=item["id"],
                    name=item["name"],
                    trailer=item["data"]["max"]
                )
                for item in response.get("results", [])
            ]
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the trailers of a game: {str(e)}")


@mcp.resource(uri="/game-details")
async def get_video_game_details(ctx: Context, game_id: int) -> GameDetailResponse:
    """
    Get details of the game.

    Args:
        game_id: An integer containing the ID of a game.
    """

    client: AsyncClient = ctx.request_context.lifespan_context

    try:
        response = await client.get(f"/games/{game_id}")
        response.raise_for_status()
        response = response.json()

        return GameDetailResponse(
            id=response["id"],
            name=response["name"],
            name_original=response["name_original"],
            description=response["description"],
            metacritic=response.get("metacritic"),
            metacritic_platforms=response.get("metacritic_platforms", []),
            released=response["released"],
            website=response["website"],
            rating=response["rating"],
            rating_top=response["rating_top"],
            ratings=response.get("ratings", []),
            playtime=response["playtime"],
            ratings_count=response["ratings_count"],
            metacritic_url=response["metacritic_url"],
            esrb_rating=response.get("esrb_rating"),
            platforms=response.get("platforms", [])
        )
    except Exception as e:
        raise ValueError(f"Error caught while fetching the details of a game: {str(e)}")
