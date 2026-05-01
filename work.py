from typing import TypedDict

class Work(TypedDict):
    name: str
    role: str
    req_author: str
    req_year: int
    req_issn: str
    req_keywords: str
    reference: str
    style: str
    doi: str
    score: int
    type: str