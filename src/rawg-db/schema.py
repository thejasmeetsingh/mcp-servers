from typing import Any

from pydantic import BaseModel


class ListBaseResponse(BaseModel):
    count: int
    current_page: int
    page_size: int


class GenreResponse(BaseModel):
    id: int
    name: str
    games_count: int
    description: str | None = None


class GenreListResponse(ListBaseResponse):
    results: list[GenreResponse]


class GameResponse(BaseModel):
    id: int
    name: str
    released: str
    rating: int | float
    playtime: int
    platforms: str
    genres: str | None = None
    esrb_rating: str | None = None
    metacritic: int | None = None


class GameListResponse(ListBaseResponse):
    results: list[GameResponse]


class GameScreenshotResponse(BaseModel):
    id: int
    image: str
    width: int
    height: int


class GameScreenshotListResponse(ListBaseResponse):
    results: list[GameScreenshotResponse]


class GameTrailerResponse(BaseModel):
    id: int
    name: str
    trailer: str


class GameTrailerListResponse(ListBaseResponse):
    results: list[GameTrailerResponse]


class GameDetailResponse(GameResponse):
    name_original: str
    description: str
    metacritic_platforms: list[dict[str, Any]]
    website: str | None
    alternative_names: list[str]
    platforms: list[dict[str, Any]]
