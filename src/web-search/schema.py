from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class WebPageExtractResult(BaseModel):
    url: str
    content: str
