"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import uuid
from typing import List, Optional, Union

import requests
from fastapi import FastAPI, status
from libgravatar import Gravatar
from pydantic import BaseModel

app = FastAPI()

class Searcher(BaseModel):
    """The structure of Searchers, used to create the data source option(s) in Videris"""
    id: str
    name: str
    hint: Optional[str] = None
    tooltip: Optional[str] = None


class Attribute(BaseModel):
    """All possible attributes that entities Videris accepts (not yet complete)"""
    Data: Optional[str] # Images
    DateOfDeath: Optional[str]
    Description: Optional[str]
    Direction: Optional[str]
    Dob: Optional[str]
    EmailAddress: Optional[str]
    FirstName: Optional[str]
    FromId: Optional[str] # Relationships
    Gender: Optional[str]
    Id: Optional[str]
    Imageuri: Optional[str]
    LastName: Optional[str]
    Name: Optional[str]
    Nationality: Optional[str]
    OtherNames: Optional[str]
    Salutation: Optional[str]
    ScreenName: Optional[str]
    Site: Optional[str]
    ToId: Optional[str] # Relationships
    Uri: Optional[str]
    Url: Optional[str]
    UserId: Optional[str]
    UserName: Optional[str]
    Username: Optional[str]
    Verified: Optional[str]


class Entity(BaseModel):
    """The structure of entities accepted by Videris"""
    id: str
    type: str
    attributes: Attribute


class Result(BaseModel):
    """The structure of each search result accepted by Videris"""
    key: str
    title: str
    subTitle: Optional[str]
    summary: Optional[str]
    source: str
    entities: Optional[List[Entity]]
    url: Optional[str]


class SearchResults(BaseModel):
    """The structure of search results accepted by Videris"""
    searchResults: List[Result]


class Error(BaseModel):
    """The structure of error messages accepted by Videris"""
    message: str


class ErrorList(BaseModel):
    """The structure of the list of errors accepted by Videris"""
    errors: List[Error]


# ============================ Shared functions ============================
def create_relationship(from_id, to_id):
    relationship = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, from_id + to_id)),
        "type": "RelationshipRelationship",
        "attributes": {
            "FromId": from_id,
            "ToId": to_id,
            "Direction": "FromTo"
        }
    }
    return relationship


def email_to_entity(email: str):
    entity = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, email)),
        "type": "EntityEmail",
        "attributes": {
            "EmailAddress": email
        }
    }

    return entity


# ============================ Little Sis functions ============================
def littlesis_build_entity(entity_type, data):
    ent_type = entity_type[6:].replace("Organisation", "Org")

    attributes = {
        "EntityPerson": {
            "Dob": "start_date",
            "DateOfDeath": "end_date"

        },
        "EntityOrganisation": {
            "Name": "name",
            "Description": "blurb"
        }
    }

    extensions = {
        "EntityPerson": {
            "FirstName": "name_first",
            "LastName": "name_last",
            "OtherNames": "name_middle",
            "Salutation": "name_prefix",
            "Gender": "gender_id"
        }
        # ,
        # "EntityOrganisation": {
        #
        # }
    }
    # print(data)
    entity = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, str(data["id"]))),
        "type": entity_type,
        "attributes": dict()
    }

    for att, src in attributes[entity_type].items():
        entity["attributes"][att] = data["attributes"][src]

    try:
        for att, src in extensions[entity_type].items():
            entity["attributes"][att] = data["attributes"]["extensions"][ent_type][src]
    except KeyError:
        pass

    if data["attributes"]["website"]:
        webpage = {
            "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, data["attributes"]["website"])),
            "type": "EntityWebPage",
            "attributes": {
                "Url": data["attributes"]["website"]
            }
        }

        return [entity, webpage]
    else:
        return [entity]


# ============================ Gravatar functions ============================
def gravatar_account_to_entity(account):
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
            "Id": "username"
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


# ============================ Shared Endpoint ============================
@app.get("/searchers/", response_model=List[Searcher], response_model_exclude_none=True)
async def get_searchers():
    searchers = [
        {
            "id": "littlesis",
            "name": "Little Sis",
            "hint": "Search for a person"
            # , "tooltip": "Find Gravatar profile by email address"
        },
        {
            "id": "gravatar",
            "name": "Gravatar",
            "hint": "Search by email address",
            "tooltip": "Find Gravatar profile by email address"
        }
    ]
    return searchers


# ============================ Little Sis Endpoint ============================
@app.get("/searchers/littlesis/results", response_model=Union[SearchResults, ErrorList],
         response_model_exclude_none=True,
         status_code=status.HTTP_200_OK)
async def get_littlesis(query: str):
    endpoint = r"https://littlesis.org/api/entities/search?q=" + query

    r = requests.get(endpoint)

    if r.status_code != 200:
        return {"errors": [{"message": r.json()}]}
    else:
        # print(r)
        data = r.json()

        search_results = []
        for i, entry in enumerate(data["data"]):
            if "Person" in entry["attributes"]["types"]:
                entity_type = "EntityPerson"
            elif "Organization" in entry["attributes"]["types"]:
                entity_type = "EntityOrganisation"
            else:
                break

            entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(entry['id'])))
            # print(entry)
            result = {
                "key": str(uuid.uuid3(uuid.NAMESPACE_DNS, query + str(i))),
                "title": entry["attributes"]["name"],
                "subTitle": entry["attributes"]["blurb"],
                "summary": entry["attributes"]["summary"],
                "source": "Little Sis",
                "entities": [],
                "url": entry["links"]["self"]
            }

            [result["entities"].append(ent) for ent in littlesis_build_entity(entity_type, entry)]

            for entity in result["entities"].copy():
                if entity["id"] != entity_uuid:
                    relationship: dict = create_relationship(entity_uuid, entity["id"])
                    result["entities"].append(relationship)

            search_results.append(result)

        output = {"searchResults": search_results}
        return output


# ============================ Gravatar Endpoint ============================
@app.get("/searchers/gravatar/results", response_model=Union[SearchResults, ErrorList],
         response_model_exclude_none=True,
         status_code=status.HTTP_200_OK)
async def get_gravatar(query: str):
    g = Gravatar(query)
    gravatar_url = g.get_image(160, "mp", False, "r")  # TODO: Learn how to create Image entities
    gravatar_profile = g.get_profile(data_format="json")
    r = requests.get(gravatar_profile)

    if r.status_code != 200:
        return {"errors": [{"message": r.json()}]}
    else:
        print(r)
        data = r.json()

        search_results = []
        for entry in data["entry"]:
            person_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, entry['id']))

            result = {
                "key": str(uuid.uuid4()),
                "title": entry["displayName"],
                "subTitle": entry["name"]["formatted"],
                "summary": f"Id: {entry['id']} | Username: {entry['preferredUsername']}",
                "source": "Gravatar",
                "entities": [
                    {
                        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, entry["thumbnailUrl"])),
                        "type": "EntityImage",
                        "attributes": {
                            "Imageuri": gravatar_url,
                            "Uri": entry["thumbnailUrl"],
                            "Data": entry["thumbnailUrl"]
                        }
                    },
                    {
                        "id": person_uuid,
                        "type": "EntityPerson",
                        "attributes": {
                            "FirstName": entry["name"]["givenName"],
                            "LastName": entry["name"]["familyName"]
                        }
                    },
                    {
                        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, entry["profileUrl"])),
                        "type": "EntityWebPage",
                        "attributes": {
                            "Url": entry["profileUrl"]
                        }
                    }
                ],
                "url": entry["profileUrl"]
            }
            if "accounts" in entry:
                for account in entry["accounts"]:
                    entity = gravatar_account_to_entity(account)
                    if entity is not None:
                        result["entities"].append(entity)

            entity: dict = email_to_entity(query.lower())
            result["entities"].append(entity)

            if "emails" in entry:
                for email in entry["emails"]:
                    if email["value"].lower() != query.lower():
                        entity = email_to_entity(email["value"].lower())
                        result["entities"].append(entity)

            for entity in result["entities"].copy():
                if entity["id"] != person_uuid:
                    relationship: dict = create_relationship(person_uuid, entity["id"])
                    result["entities"].append(relationship)

            search_results.append(result)

        output = {"searchResults": search_results}
        # print(output)
        return output

    # Open url in default browser
    # webbrowser.open(gravatar_url, new=2)
