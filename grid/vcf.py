import uuid
from typing import List, Optional

from pydantic import BaseModel


class Searcher(BaseModel):
    """The structure of Searchers, used to create the data source option(s) in Videris"""
    id: str
    name: str
    hint: Optional[str] = None
    tooltip: Optional[str] = None


class Attribute(BaseModel):
    """All possible attributes that entities Videris accepts (not yet complete)"""
    Category: Optional[str]
    City: Optional[str]
    CompaniesHouseId: Optional[str]
    CompanyNumber: Optional[str]
    Compliance: Optional[str]
    Country: Optional[str]
    Data: Optional[str]  # Images
    Date: Optional[str]
    DateOfDeath: Optional[str]
    Description: Optional[str]
    Direction: Optional[str]
    Dob: Optional[str]
    Duns: Optional[str]
    EmailAddress: Optional[str]
    FirstName: Optional[str]
    FromId: Optional[str]  # Relationships
    Gender: Optional[str]
    Id: Optional[str]
    Imageuri: Optional[str]
    IncorporationDate: Optional[str]
    IsCompany: Optional [str]
    JobTitle: Optional[str]
    LastName: Optional[str]
    Liquidated: Optional[str]
    LocalName: Optional[str]
    Name: Optional[str]
    Nationality: Optional[str]
    NumberOfShares: Optional[str]
    OtherNames: Optional[str]
    PhoneNumbers: Optional[str]
    Postcode: Optional[str]
    Region: Optional[str]
    RegistrationState: Optional[str]
    RegistrationCountry: Optional[str]
    Salutation: Optional[str]
    ScreenName: Optional[str]
    SicCode: Optional[str]
    Site: Optional[str]
    Status: Optional[str]
    StatusSince: Optional[str]
    Street1: Optional[str]
    Street2: Optional[str]
    Street3: Optional[str]
    Text: Optional[str]
    Title: Optional[str]  # Relationships
    ToId: Optional[str]  # Relationships
    TradeDescription: Optional[str]
    Uri: Optional[str]
    Url: Optional[str]
    UserId: Optional[str]
    UserName: Optional[str]
    Username: Optional[str]
    VatNumber: Optional[str]
    Verified: Optional[str]
    WorldCompliance: Optional[str]


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


class Error(BaseModel):
    """The structure of error messages accepted by Videris"""
    message: str


class SearchResults(BaseModel):
    """The structure of search results accepted by Videris"""
    searchResults: Optional[List[Result]]
    errors: Optional[List[Error]]


# ============================ Shared functions ============================
def create_relationship(from_id: str, to_id: str, title: str = "") -> dict:
    """
    Creates a relationship "entity" between the specified entity ids with an optional description.

    :param from_id: UUID of "from" entity
    :type from_id: str
    :param to_id: UUID of "to" entity
    :type to_id: str
    :param title: Description of the relationship OPTIONAL
    :type title: str
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
            "Title": title
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
