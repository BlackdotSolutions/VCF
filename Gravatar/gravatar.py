"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import uuid

import requests
from libgravatar import Gravatar

from vcf import create_relationship, email_to_entity

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


async def get_gravatar(query: str, max_results=100):
    g = Gravatar(query)
    # gravatar_url = g.get_image(160, "mp", False, "r")   TODO: Learn how to create Image entities
    gravatar_profile = g.get_profile(data_format="json")
    r = requests.get(gravatar_profile)
    output = dict()
    if r.status_code != 200:
        return {"errors": [{"message": r.json()}]}
    else:
        # print(r)
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

        output["searchResults"] = search_results
        # print(output)
        return output

    # Open url in default browser
    # webbrowser.open(gravatar_url, new=2)
