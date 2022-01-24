import uuid
from typing import List, Optional, Union
import json
import requests
from fastapi import FastAPI, status
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
    Id: Optional[str]
    Site: Optional[str]
    ScreenName: Optional[str]
    Verified: Optional[str]
    EmailAddress: Optional[str]
    FromId: Optional[str]
    ToId: Optional[str]
    Direction: Optional[str]
    Nationality: Optional[str]
    Name: Optional[str]
    Description: Optional[str]
    DateOfDeath: Optional[str]
    Dob: Optional[str]
    Salutation: Optional[str]
    OtherNames: Optional[str]


class Entity(BaseModel):
    id: str
    type: str
    attributes: Attribute


class Result(BaseModel):
    key: str
    title: str
    subTitle: Optional[str]
    summary: Optional[str]
    source: str
    entities: Optional[List[Entity]]
    url: Optional[str]


class SearchResults(BaseModel):
    searchResults: List[Result]


class Error(BaseModel):
    message: str


class ErrorList(BaseModel):
    errors: List[Error]


def build_entity(entity_type, data):
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
            "Salutation": "name_prefix"
            # ,
            # "Gender": "gender_id"
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


@app.get("/searchers/", response_model=List[Searcher], response_model_exclude_none=True)
async def get_searchers():
    searchers = [
        {
            "id": "littlesis",
            "name": "Little Sis",
            "hint": "Search for a person"
            # , "tooltip": "Find Gravatar profile by email address"
        }
    ]
    return searchers


@app.get("/searchers/littlesis/results", response_model=Union[SearchResults, ErrorList],
         response_model_exclude_none=True,
         status_code=status.HTTP_200_OK)
async def get_entities(query: str):
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

            [result["entities"].append(ent) for ent in build_entity(entity_type, entry)]

            for entity in result["entities"].copy():
                if entity["id"] != entity_uuid:
                    relationship: dict = create_relationship(entity_uuid, entity["id"])
                    result["entities"].append(relationship)

            search_results.append(result)

        output = {"searchResults": search_results}
        return output
