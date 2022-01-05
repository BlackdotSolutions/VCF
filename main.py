# import code for encoding urls and generating md5 hashes

import uuid
from typing import List, Optional

import requests
from fastapi import FastAPI
from libgravatar import Gravatar
from pydantic import BaseModel

app = FastAPI()


class Searcher(BaseModel):
    id: str
    name: str
    hint: Optional[str] = None
    tooltip: Optional[str] = None


class Attribute(BaseModel):
    Imageuri: Optional[str]
    Uri: Optional[str]
    FirstName: Optional[str]
    LastName: Optional[str]


class Entity(BaseModel):
    id: str
    type: str
    attributes: Attribute


class Result(BaseModel):
    key: str
    title: str
    subTitle: str
    summary: str
    source: str
    entities: List[Entity]
    url: str


class SearchResults(BaseModel):
    searchResults: List[Result]


@app.get("/searchers/", response_model=List[Searcher], response_model_exclude_none=True)
async def get_searchers():
    searchers = [
        {
            "id": "gravatar",
            "name": "Gravatar",
            "hint": "Search by email address",
            "tooltip": "Find Gravatar profile by email address"
        }
    ]
    return searchers


@app.get("/searchers/gravatar/results", response_model=SearchResults, response_model_exclude_none=True)
async def get_gravatar(query: str):
    g = Gravatar(query)
    gravatar_url = g.get_image()
    gravatar_profile = g.get_profile(data_format="json")
    r = requests.get(gravatar_profile)

    if r.status_code != 200:
        return r
    else:
        print(r)
        data = r.json()

        searchResults = []
        for entry in data["entry"]:
            result = {
                "key": str(uuid.uuid4()),
                "title": entry["displayName"],
                "subTitle": entry["name"]["formatted"],
                "summary": f"Id: {entry['id']}\nUsername: {entry['preferredUsername']}",
                "source": "Gravatar",
                "entities": [
                    # {
                    #     "id": str(uuid.uuid4()),
                    #     "type": "EntityImage",
                    #     "attributes": {
                    #         "Imageuri": entry["thumbnailUrl"],
                    #         "Uri": entry["thumbnailUrl"]
                    #     }
                    # },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "EntityPerson",
                        "attributes": {
                            "FirstName": entry["name"]["givenName"],
                            "LastName": entry["name"]["familyName"]
                        }
                    }
                ],
                "url": entry["profileUrl"]
            }
            searchResults.append(result)
            output = {"searchResults": searchResults}
        return output

# Open url in default browser
# webbrowser.open(gravatar_url, new=2)
