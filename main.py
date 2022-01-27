"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import json
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
    Data: Optional[str]  # Images
    DateOfDeath: Optional[str]
    Description: Optional[str]
    Direction: Optional[str]
    Dob: Optional[str]
    EmailAddress: Optional[str]
    FirstName: Optional[str]
    FromId: Optional[str]  # Relationships
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
    ToId: Optional[str]  # Relationships
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
def create_relationship(from_id: str, to_id: str, description: str = "") -> dict:
    """
    Creates a relationship "entity" between the specified entity ids with an optional description.

    :param from_id: UUID of "from" entity
    :type from_id: str
    :param to_id: UUID of "to" entity
    :type to_id: str
    :param description: Description of the relationship OPTIONAL
    :type description: str
    :return: Structured relationship entity
    :rtype: dict
    """

    relationship = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, from_id + to_id)),
        "type": "RelationshipRelationship",
        "attributes": {
            "FromId": from_id,
            "ToId": to_id,
            "Direction": "FromTo",
            "Description": description
        }
    }
    return relationship


def email_to_entity(email: str):
    """
    Creates an email entity.

    :param email: Email address
    :type email: str
    :return: Structured email entity
    :rtype: dict
    """

    entity = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, email)),
        "type": "EntityEmail",
        "attributes": {
            "EmailAddress": email
        }
    }

    return entity


# ============================ Little Sis functions ============================
def littlesis_build_entity(data):
    # print(data["attributes"].keys())
    ent_type = data["attributes"]["primary_ext"]  # Little Sis entity type
    v_entity_type = "Entity" + ent_type.replace("Org", "Organisation")  # Videris entity type
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

    entity = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, str(data["id"]))),
        "type": v_entity_type,
        "attributes": dict()
    }

    for att, src in attributes[v_entity_type].items():
        entity["attributes"][att] = data["attributes"][src]

    try:
        for att, src in extensions[v_entity_type].items():
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
        relationship = create_relationship(entity["id"], webpage["id"])
        return [entity, webpage, relationship]
    else:
        return [entity]


def get_littlesis_endpoint(endpoint_name, entity_id=None, category_id=None, page=None):
    endpoint = r"https://littlesis.org/api/entities"
    if entity_id:
        endpoint += "/" + str(entity_id)

    if endpoint_name:
        endpoint += "/" + endpoint_name

    params_used = False

    if category_id:
        endpoint += "?=category_id" + category_id
        params_used = True

    if page:
        if params_used:
            endpoint += "&page=" + str(page)
        else:
            endpoint += "?page=" + str(page)

    r = requests.get(endpoint)
    if r.status_code != 200:
        raise Exception("Bad API response: " + str(r.status_code) + " - " + r.json())
    else:
        meta = r.json()["meta"] if r.json()["meta"] else None
        data = r.json()["data"]
        return meta, data


def get_littlesis_network(entity_id):
    categories = ["1", "2", "3", "4", "6", "7", "8", "9", "10", "11", "12"]
    entities = []

    # Get relationships for provided entity
    relationships_data = []
    for category_id in categories:
        try:
            meta, data = get_littlesis_endpoint("relationships", entity_id, category_id)
            relationships_data += data
        except Exception as e:
            print(e)
            break
        while meta["currentPage"] < meta["currentPage"]:
            try:
                meta, data = get_littlesis_endpoint("relationships", entity_id, category_id, meta["currentPage"] + 1)
                relationships_data += data
            except Exception as e:
                print(e)
                break

    # Get connections for provided entity
    connections_data = []
    for category_id in categories:
        page = 1
        try:
            meta, data = get_littlesis_endpoint("connections", entity_id, category_id, page)
            relationships_data += data
        except Exception as e:
            print(e)
            break
        while data != []:
            page += 1
            try:
                meta, data = get_littlesis_endpoint("relationships", entity_id, category_id, page)
                relationships_data += data
            except Exception as e:
                print(e)
                break

    for connection in connections_data:
        entities += littlesis_build_entity(connection)

    for relationship in relationships_data:
        from_entity_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(relationship["attributes"]["entity1_id"])))
        to_entity_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(relationship["attributes"]["entity2_id"])))
        description = relationship["attributes"]["description1"]
        entities.append(create_relationship(from_entity_id, to_entity_id, description))

    return entities


# ============================ Gravatar functions ============================
def gravatar_account_to_entity(account):
    """Converts gravatar JSON for social media accounts to their respective Videris entities."""
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
    """Searches Little Sis API. Auto-enriches top 10 results to fetch connections of the found entity."""

    endpoint = r"https://littlesis.org/api/entities/search?q=" + query
    r = requests.get(endpoint)

    if r.status_code != 200:
        return {"errors": [{"message": r.json()}]}
    else:
        data = r.json()["data"]

        search_results = []
        for i, entry in enumerate(data):
            if "Person" not in entry["attributes"]["types"] and "Organization" not in entry["attributes"]["types"]:
                break

            entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(entry["id"])))

            result = {
                "key": str(uuid.uuid3(uuid.NAMESPACE_DNS, query + str(i))),
                "title": entry["attributes"]["name"],
                "subTitle": entry["attributes"]["blurb"],
                "summary": entry["attributes"]["summary"],
                "source": "Little Sis",
                "entities": [],
                "url": entry["links"]["self"]
            }

            # Add the entity/entities from the search results
            [result["entities"].append(ent) for ent in littlesis_build_entity(entry)]

            # For the top 10 results
            if i < 10:
                # Query their network and return related entities
                [result["entities"].append(ent) for ent in get_littlesis_network(entry["id"])]

            # for entity in result["entities"].copy():
            #     if str(entity["id"]) != entity_uuid and entity["type"] not in ["EntityWebPage",
            #                                                                    "RelationshipRelationship"]:
            #         print("Creating relationship to a(n) " + entity["type"])
            #         relationship: dict = create_relationship(entity_uuid, str(entity["id"]))
            #         result["entities"].append(relationship)

            search_results.append(result)

        output = {"searchResults": search_results}
        print(json.dumps(output))
        return output


# ============================ Gravatar Endpoint ============================
@app.get("/searchers/gravatar/results", response_model=Union[SearchResults, ErrorList],
         response_model_exclude_none=True,
         status_code=status.HTTP_200_OK)
async def get_gravatar(query: str):
    g = Gravatar(query)
    # gravatar_url = g.get_image(160, "mp", False, "r")   TODO: Learn how to create Image entities
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

            # Get names
            formatted_name, first_name, last_name = ("", "", "")  # Blank names by default

            # Check if the response contains name info
            if "name" not in entry:
                # If not, use the username
                formatted_name = entry["preferredUsername"]
                first_name = entry["preferredUsername"]
            elif entry["name"] != []:
                # If there is non-empty name object, then use that
                formatted_name = entry["name"]["formatted"]
                first_name = entry["name"]["givenName"]
                last_name = entry["name"]["familyName"]

            # Create search result
            result = {
                "key": str(uuid.uuid4()),
                "title": entry["displayName"],
                "subTitle": formatted_name,
                "summary": f"Id: {entry['id']} | Username: {entry['preferredUsername']}",
                "source": "Gravatar",
                "entities": [
                    # TODO Learn how to create Image entities
                    # {
                    #     "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, entry["thumbnailUrl"])),
                    #     "type": "EntityImage",
                    #     "attributes": {
                    #         "Imageuri": gravatar_url,
                    #         "Uri": entry["thumbnailUrl"],
                    #         "Data": entry["thumbnailUrl"]
                    #     }
                    # },
                    {
                        "id": person_uuid,
                        "type": "EntityPerson",
                        "attributes": {
                            "FirstName": first_name,
                            "LastName": last_name
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

            # If the profile has info about online accounts then capture that
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
