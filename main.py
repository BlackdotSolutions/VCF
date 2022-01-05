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
    Url: Optional[str]
    UserName: Optional[str]
    Username: Optional[str]
    UserId: Optional[str]
    Site: Optional[str]
    ScreenName: Optional[str]
    Verified: Optional[str]


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


def account_to_entity(account):
    shortname = account["shortname"]

    shortname_to_entity = {
        "flickr": "EntityFlickrProfile",
        "facebook": "EntityFacebookProfile",
        "goodreads": "EntityOnlineIdentity",
        "tumblr": "EntityOnlineIdentity",
        "twitter": "EntityTwitterProfile",
        "wordpress": "EntityWebPage"}

    attributes = {
        "facebook": {
            "Url": "url",
            "Username": "username"
        },
        "flickr": {
            "Url": "url",
            "Username": "username"
        },
        "goodreads": {
            "Url": "url",
            "Site": "domain",
            "UserName": "userid"
        },
        "tumblr": {
            "Url": "url",
            "Site": "domain",
            "UserName": "username",
            "ScreenName": "display"
        },
        "twitter": {
            "Url": "url",
            "Username": "username",
            "Verified": "verified"
        },
        "wordpress": {
            "Url": "url"
        }
    }

    if shortname not in shortname_to_entity.keys():
        return None
    else:
        entity = {
            "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, account["url"])),
            "type": shortname_to_entity[shortname],
            "attributes": dict()
        }

        for att, src in attributes[shortname].items():
            entity["attributes"][att] = account[src]

        return entity


def email_to_entity(email: str):
    entity = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, email)),
        "type": "EntityEmail",
        "attributes": {
            "EmailAddress": email
        }
    }

    return entity


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
                    #     "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, entry["thumbnailUrl"])),
                    #     "type": "EntityImage",
                    #     "attributes": {
                    #         "Imageuri": entry["thumbnailUrl"],
                    #         "Uri": entry["thumbnailUrl"],
                    #         "Data": img_data
                    #     }
                    # },
                    {
                        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, entry['id'])),
                        "type": "EntityPerson",
                        "attributes": {
                            "FirstName": entry["name"]["givenName"],
                            "LastName": entry["name"]["familyName"]
                        }
                    }
                ],
                "url": entry["profileUrl"]
            }

            for account in entry["accounts"]:
                entity = account_to_entity(account)
                if entity is not None:
                    result["entities"].append(entity)

            entity = email_to_entity(query.lower())
            result["entities"].append(entity)

            for email in entry["emails"]:
                if email["value"].lower() != query.lower():
                    entity = email_to_entity(email["value"].lower())
                    result["entities"].append(entity)

            searchResults.append(result)
            output = {"searchResults": searchResults}

        return output

# Open url in default browser
# webbrowser.open(gravatar_url, new=2)
