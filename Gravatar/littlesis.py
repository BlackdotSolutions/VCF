"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import uuid

import requests

from vcf import create_relationship


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


def get_littlesis_endpoint(endpoint_name, entity_id=None, query=None, category_id=None, page=None):
    endpoint = r"https://littlesis.org/api/entities"

    if entity_id:
        endpoint += "/" + str(entity_id)

    if endpoint_name:
        endpoint += "/" + endpoint_name

    params_used = False

    if query:
        endpoint += "?q=" + query
        params_used = True

    if category_id:
        if params_used:
            endpoint += "&category_id=" + category_id
        else:
            endpoint += "?category_id=" + category_id
            params_used = True

    if page:
        if params_used:
            endpoint += "&page=" + str(page)
        else:
            endpoint += "?page=" + str(page)
            params_used = True

    r = requests.get(endpoint)
    print(endpoint + " : " + str(r.status_code))
    if r.status_code != 200:
        raise Exception(endpoint + " - Bad API response: " + str(r.status_code))
    else:
        meta = r.json()["meta"] if r.json()["meta"] else None
        data = r.json()["data"]
        return meta, data


def get_littlesis_network(entity_id: int):
    """
    Queries Little Sis endpoints for connections and relationships to/from the specified entity id.

    :param entity_id: LittleSis ID of the entity which we want to build out the network for.
    :type entity_id: int
    :return: List of entities (including relationships) that represent the entity's network.
    :rtype: list(dict)
    """
    # categories = ["1", "2", "3", "4", "6", "7", "8", "9", "10", "11", "12"]
    entities = []

    # Get connections for provided entity
    connections_data = []
    # for category_id in categories:
    page = 1
    try:
        meta, data = get_littlesis_endpoint("connections", entity_id=entity_id, page=page)
        connections_data += data

        # while data and page <= 3:
        #     page += 1
        #     meta, data = get_littlesis_endpoint("connections", entity_id, page=page)
        #     connections_data += data
    except Exception as e:
        print(e)

    if not connections_data:
        return []

    for connection in connections_data:
        entities += littlesis_build_entity(connection)

    # Get relationships for provided entity
    relationships_data = []
    # for category_id in categories:
    try:
        meta, data = get_littlesis_endpoint("relationships", entity_id=entity_id)
        relationships_data += data
        while meta["currentPage"] < meta["pageCount"] and meta["currentPage"] < 3:
            meta, data = get_littlesis_endpoint("relationships", entity_id=entity_id, page=meta["currentPage"] + 1)
            relationships_data += data
    except Exception as e:
        print(e)

    source_entity_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(entity_id)))

    # Get a list of all entities that need relationships building for them
    entity_ids = []
    for item in entities:
        # We don't want to create relationships to relationships so exclude those.
        if item["type"] != "RelationshipRelationship":
            entity_ids.append(item["id"])

    for relationship in relationships_data:

        from_entity_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(relationship["attributes"]["entity1_id"])))
        to_entity_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(relationship["attributes"]["entity2_id"])))
        if (from_entity_id == source_entity_id and to_entity_id in entity_ids) or (
                to_entity_id == source_entity_id and from_entity_id in entity_ids):

            description = relationship["attributes"]["description1"]
            entities.append(create_relationship(from_entity_id, to_entity_id, description))

            if from_entity_id == source_entity_id:
                entity_ids.remove(to_entity_id)
            else:
                entity_ids.remove(from_entity_id)

    # All entities now have detailed relationship info where available
    # Need to remove webpage entities which have already been linked to their associates entities
    for e in entities:
        if e["type"] not in ["EntityPerson", "EntityOrganisation"] and e["id"] in entity_ids:
            entity_ids.remove(e["id"])

    # Build relationships to the source entity for all that is left
    for remaining_entity_id in entity_ids:
        entities.append(create_relationship(source_entity_id, remaining_entity_id))

    return entities


async def get_littlesis(query: str, max_results: int):
    """Searches Little Sis API. Auto-enriches top 10 results to fetch connections of the found entity."""
    max_results = int(max_results)
    output = dict()
    output["errors"] = []
    try:
        meta, data = get_littlesis_endpoint("search", query=query)
    except Exception as e:
        return {"errors": [{"message": str(e)}]}

    while meta["currentPage"] < meta["pageCount"] and len(data) < max_results:
        try:
            meta, search_data = get_littlesis_endpoint("search", query=query, page=meta["currentPage"] + 1)
            data += search_data
        except Exception:
            output["errors"].append({"message": "Unable to fetch some results from Little Sis. Please try again."})

    search_results = []
    for i, entry in enumerate(data):
        # entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(entry["id"])))

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
        result["entities"] += littlesis_build_entity(entry)

        # For the top 10 results
        if i < 10:
            # Query their network and return related entities
            result["entities"] += get_littlesis_network(entry["id"])

        # for entity in result["entities"].copy():
        #     if str(entity["id"]) != entity_uuid and entity["type"] not in ["EntityWebPage",
        #                                                                    "RelationshipRelationship"]:
        #         print("Creating relationship to a(n) " + entity["type"])
        #         relationship: dict = create_relationship(entity_uuid, str(entity["id"]))
        #         result["entities"].append(relationship)

        search_results.append(result)

    output["searchResults"] = search_results
    # print(json.dumps(output))
    return output
