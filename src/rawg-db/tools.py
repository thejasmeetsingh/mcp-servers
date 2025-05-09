import os
import json
from contextlib import asynccontextmanager

import redis.asyncio as redis
from httpx import AsyncClient
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

from schema import (
    GenreResponse,
    GenreListResponse,
    GameResponse,
    GameListResponse,
    GameScreenshotResponse,
    GameScreenshotListResponse,
    GameTrailerResponse,
    GameTrailerListResponse,
    GameDetailResponse
)
from utils import convert_dict_to_markdown


# Load env variables located in .env file
load_dotenv()
BASE_URL = os.getenv("RAWG_API_BASE_URL")
API_KEY = os.getenv("RAWG_API_KEY")

RAWG_RESULT_PAGE_SIZE = 10
CACHE_EXP = 3600


@asynccontextmanager
async def lifespan(_: FastMCP):
    """
    Initialize an async httpx client which will part of the request content.
    And it'll be used in all the methods for fetching data from RAWG API service
    """

    if not BASE_URL or not API_KEY:
        raise ValueError("RAWG API service credentials are not configured in the environment."
                         "Please check your environment variables and try again.")

    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "rawg-db-mcp/1.0"
        }

        default_params = {
            "key": API_KEY,
            "page_size": RAWG_RESULT_PAGE_SIZE
        }

        client = AsyncClient(
            base_url=BASE_URL,
            headers=headers,
            params=default_params,
            timeout=30
        )
        cache = await redis.Redis(host="redis", decode_responses=True)

        yield {"client": client, "cache": cache}
    except Exception as e:
        print(e)
        raise ValueError(str(e)) from e
    finally:
        await client.aclose()
        await cache.aclose()


# Create MCP server instance
mcp = FastMCP(name="rawg-db", lifespan=lifespan)


@mcp.tool()
async def get_video_games_genre_list(ctx: Context, page: int = 1) -> str:
    """
    Get list of video game genres. Like: Action, Adventure, Indie etc

    Args:
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context["client"]
    cache: redis.Redis = ctx.request_context.lifespan_context["cache"]

    try:
        # Fetch the data from the cache first
        key = f"genres:{page}"
        response = await cache.get(key)

        # Parsed the data if found in cache else retrieve the data from API
        # And set it into cache
        if response:
            response = json.loads(response)
        else:
            response = await client.get("/genres", params={"page": page})
            response.raise_for_status()
            response = response.json()

            await cache.set(key, json.dumps(response), ex=CACHE_EXP)

        await ctx.report_progress(75, 100)

        result = GenreListResponse(
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
        ).model_dump()

        return convert_dict_to_markdown(result)

    except Exception as e:
        raise ValueError(
            f"Error caught while fetching the genre list: {str(e)}") from e


@mcp.tool()
async def get_video_games_list(
    ctx: Context,
    page: int = 1,
    search: str | None = None,
    genres: str | None = None,
    dates: str | None = None,
    metacritic: str | None = None,
    ordering: str | None = None
) -> str:
    """
    Get list of a video games.

    Args:
        page: An integer representing the page number that needs to be fetched from the service.
        search: An optional string which contains the search query.

        genres: An optional comma-separated string,
                To perform filter on the games list by genre IDs or names.
                Like: action or action,indie.

        dates: An optional comma-separated string,
                To perform filter on the games list by release date.
                Like: 2010-01-01,2018-12-31 or 2010-01-01

        metacritic: An optional comma-separated string,
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

    client: AsyncClient = ctx.request_context.lifespan_context["client"]

    try:
        params = {"page": page, "exclude_stores": True}

        # Update the query params based on if they actually contain some value.
        if search:
            params.update({"search": search})
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

        result = GameListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GameResponse(
                    id=item["id"],
                    name=item["name"],
                    released=item["released"],
                    rating=item["rating"],
                    playtime=item["playtime"],
                    metacritic=item.get("metacritic"),
                    esrb_rating=item["esrb_rating"]["name"] if item.get(
                        "esrb_rating") else None,
                    genres=",".join(
                        genre["name"]
                        for genre in response.get("genres", [])
                    ),
                    platforms=",".join(
                        platform["platform"]["name"]
                        for platform in item.get("platforms", [])
                    ),
                )
                for item in response.get("results", [])
            ]
        ).model_dump()

        return convert_dict_to_markdown(result)

    except Exception as e:
        raise ValueError(
            f"Error caught while fetching the games list: {str(e)}") from e


@mcp.tool()
async def get_video_game_additions(ctx: Context, game_id: int, page: int = 1) -> str:
    """
    Get a list of additions or DLC's for the given game ID, GOTY and other editions,
    companion apps, etc.

    Args:
        game_id: An integer containing the ID of a game.
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context["client"]
    cache: redis.Redis = ctx.request_context.lifespan_context["cache"]

    try:
        # Fetch the data from the cache first
        key = f"additions/{game_id}:{page}"
        response = await cache.get(key)

        # Parsed the data if found in cache else retrieve the data from API
        # And set it into cache
        if response:
            response = json.loads(response)
        else:
            response = await client.get(f"/games/{game_id}/additions", params={"page": page})
            response.raise_for_status()
            response = response.json()

            await cache.set(key, json.dumps(response), ex=CACHE_EXP)

        result = GameListResponse(
            count=response["count"],
            current_page=page,
            page_size=RAWG_RESULT_PAGE_SIZE,
            results=[
                GameResponse(
                    id=item["id"],
                    name=item["name"],
                    released=item["released"],
                    rating=item["rating"],
                    playtime=item["playtime"],
                    metacritic=item.get("metacritic"),
                    esrb_rating=item["esrb_rating"]["name"] if item.get(
                        "esrb_rating") else None,
                    genres=",".join(
                        genre["name"]
                        for genre in response.get("genres", [])
                    ),
                    platforms=",".join(
                        platform["platform"]["name"]
                        for platform in item.get("platforms", [])
                    ),
                )
                for item in response.get("results", [])
            ]
        ).model_dump()

        return convert_dict_to_markdown(result)

    except Exception as e:
        raise ValueError(
            f"Error caught while fetching the additions of a game: {str(e)}") from e


@mcp.tool()
async def get_video_game_screenshots(
    ctx: Context,
    game_id: int,
    page: int = 1
) -> str:
    """
    Get screenshots or images for the given game ID.

    Args:
        game_id: An integer containing the ID of a game.
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context["client"]
    cache: redis.Redis = ctx.request_context.lifespan_context["cache"]

    try:
        # Fetch the data from the cache first
        key = f"screenshots/{game_id}:{page}"
        response = await cache.get(key)

        # Parsed the data if found in cache else retrieve the data from API
        # And set it into cache
        if response:
            response = json.loads(response)
        else:
            response = await client.get(f"/games/{game_id}/screenshots", params={"page": page})
            response.raise_for_status()
            response = response.json()

            await cache.set(key, json.dumps(response), ex=CACHE_EXP)

        result = GameScreenshotListResponse(
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
        ).model_dump()

        return convert_dict_to_markdown(result)

    except Exception as e:
        raise ValueError(
            f"Error caught while fetching the screenshots of a game: {str(e)}") from e


@mcp.tool()
async def get_video_game_trailers(
    ctx: Context,
    game_id: int,
    page: int = 1
) -> str:
    """
    Get a list of trailers/movies/gameplay etc of a given game ID.

    Args:
        game_id: An integer containing the ID of a game.
        page: An integer representing the page number that needs to be fetched from the service.
    """

    client: AsyncClient = ctx.request_context.lifespan_context["client"]
    cache: redis.Redis = ctx.request_context.lifespan_context["cache"]

    try:
        # Fetch the data from the cache first
        key = f"movies/{game_id}:{page}"
        response = await cache.get(key)

        # Parsed the data if found in cache else retrieve the data from API
        # And set it into cache
        if response:
            response = json.loads(response)
        else:
            response = await client.get(f"/games/{game_id}/movies", params={"page": page})
            response.raise_for_status()
            response = response.json()

            await cache.set(key, json.dumps(response), ex=CACHE_EXP)

        result = GameTrailerListResponse(
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
        ).model_dump()

        return convert_dict_to_markdown(result)

    except Exception as e:
        raise ValueError(
            f"Error caught while fetching the trailers of a game: {str(e)}") from e


@mcp.tool()
async def get_video_game_details(ctx: Context, game_id: int) -> str:
    """
    Get details of the game.

    Args:
        game_id: An integer containing the ID of a game.
    """

    client: AsyncClient = ctx.request_context.lifespan_context["client"]
    cache: redis.Redis = ctx.request_context.lifespan_context["cache"]

    try:
        # Fetch the data from the cache first
        key = f"games/{game_id}"
        response = await cache.get(key)

        # Parsed the data if found in cache else retrieve the data from API
        # And set it into cache
        if response:
            response = json.loads(response)
        else:
            response = await client.get(f"/games/{game_id}")
            response.raise_for_status()
            response = response.json()

            await cache.set(key, json.dumps(response), ex=CACHE_EXP)

        result = GameDetailResponse(
            id=response["id"],
            name=response["name"],
            name_original=response["name_original"],
            alternative_names=response.get("alternative_names", []),
            description=response["description"],
            metacritic=response.get("metacritic"),
            metacritic_platforms=[
                {
                    "metascore": metacritic_platform["metascore"],
                    "platform": metacritic_platform["platform"]["name"]
                }
                for metacritic_platform in response.get("metacritic_platforms", [])
            ],
            released=response["released"],
            website=response["website"] if response["website"] else None,
            rating=response["rating"],
            playtime=response["playtime"],
            esrb_rating=response["esrb_rating"]["name"] if response.get(
                "esrb_rating") else None,
            platforms=[
                {
                    "name": platform["platform"]["name"],
                    "released_at": platform["released_at"],
                    "requirements": platform["requirements"]
                }
                for platform in response.get("platforms", [])
            ]
        ).model_dump()

        return convert_dict_to_markdown(result)

    except Exception as e:
        raise ValueError(
            f"Error caught while fetching the details of a game: {str(e)}") from e
