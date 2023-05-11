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
    """All possible attributes that entities Videris accepts"""
    class Config:
        extra = Extra.forbid

    None_: Optional[Any] = Field(None, alias='None')
    FromId: Optional[Any] = None
    ToId: Optional[Any] = None
    Address: Optional[Any] = None
    Album: Optional[Any] = None
    AlexaRank: Optional[Any] = None
    AlternateName: Optional[Any] = None
    Annotator1Imageuri: Optional[Any] = None
    Apn: Optional[Any] = None
    AreaCode: Optional[Any] = None
    Bio: Optional[Any] = None
    Biography: Optional[Any] = None
    Birthday: Optional[Any] = None
    Brand: Optional[Any] = None
    BuildDate: Optional[Any] = None
    BvdId: Optional[Any] = None
    CallSign: Optional[Any] = None
    Cancelled: Optional[Any] = None
    Caption: Optional[Any] = None
    Category: Optional[Any] = None
    Charges: Optional[Any] = None
    City: Optional[Any] = None
    Closed: Optional[Any] = None
    Collectionid: Optional[Any] = None
    Colour: Optional[Any] = None
    CommentCount: Optional[Any] = None
    Comments: Optional[Any] = None
    CompaniesHouseId: Optional[Any] = None
    CompanyNumber: Optional[Any] = None
    CompanySize: Optional[Any] = None
    Compliance: Optional[Any] = None
    Confidence: Optional[Any] = None
    Connections: Optional[Any] = None
    Content: Optional[Any] = None
    ContributorsEnabled: Optional[Any] = None
    Coordinates: Optional[Any] = None
    CorrectedNumber: Optional[Any] = None
    Count: Optional[Any] = None
    Country: Optional[Any] = None
    CountryCode: Optional[Any] = None
    CreatedAt: Optional[Any] = None
    CreatedDate: Optional[Any] = None
    CreatedTime: Optional[Any] = None
    Data: Optional[Any] = None
    Date: Optional[Any] = None
    DateOfDeath: Optional[Any] = None
    DateOfIssue: Optional[Any] = None
    Deactivated: Optional[Any] = None
    Description: Optional[Any] = None
    DescriptionText: Optional[Any] = None
    Digits: Optional[Any] = None
    Direction: Optional[Any] = None
    Disqualifications: Optional[Any] = None
    DnbRoleId: Optional[Any] = None
    Dob: Optional[Any] = None
    DocumentId: Optional[Any] = None
    DocumentNumber: Optional[Any] = None
    DocumentType: Optional[Any] = None
    Domain: Optional[Any] = None
    DomainName: Optional[Any] = None
    Duns: Optional[Any] = None
    Education: Optional[Any] = None
    EmailAddress: Optional[Any] = None
    EmailAddresses: Optional[Any] = None
    Encoding: Optional[Any] = None
    EndTime: Optional[Any] = None
    FamilyMembers: Optional[Any] = None
    Favorited: Optional[Any] = None
    FavouritesCount: Optional[Any] = None
    FilingNumber: Optional[Any] = None
    FirstName: Optional[Any] = None
    FollowersCount: Optional[Any] = None
    FollowingCount: Optional[Any] = None
    Format: Optional[Any] = None
    FormattedNumber: Optional[Any] = None
    FriendCount: Optional[Any] = None
    FullAddress: Optional[Any] = None
    FullUrl: Optional[Any] = None
    Gender: Optional[Any] = None
    GeoEnabled: Optional[Any] = None
    Groups: Optional[Any] = None
    Hashtags: Optional[Any] = None
    HeartsCount: Optional[Any] = None
    HomeTown: Optional[Any] = None
    Html: Optional[Any] = None
    Id: Optional[Any] = None
    Image: Optional[Any] = None
    Imageuri: Optional[Any] = None
    Imei: Optional[Any] = None
    ImoNumber: Optional[Any] = None
    IncorporationDate: Optional[Any] = None
    Industry: Optional[Any] = None
    InsolvencyHistory: Optional[Any] = None
    Interests: Optional[Any] = None
    IpAddress: Optional[Any] = None
    IsCompany: Optional[Any] = None
    JobTitle: Optional[Any] = None
    Kind: Optional[Any] = None
    Language: Optional[Any] = None
    Languages: Optional[Any] = None
    LastName: Optional[Any] = None
    LastSeen: Optional[Any] = None
    LikeCount: Optional[Any] = None
    Liquidated: Optional[Any] = None
    ListedCount: Optional[Any] = None
    LiveListing: Optional[Any] = None
    Locale: Optional[Any] = None
    LocalName: Optional[Any] = None
    LocalNumber: Optional[Any] = None
    LocalPart: Optional[Any] = None
    Location: Optional[Any] = None
    Make: Optional[Any] = None
    Members: Optional[Any] = None
    MetaDescription: Optional[Any] = None
    MetaKeywords: Optional[Any] = None
    Model: Optional[Any] = None
    Name: Optional[Any] = None
    Nationality: Optional[Any] = None
    NationalNumber: Optional[Any] = None
    Network: Optional[Any] = None
    Number: Optional[Any] = None
    NumberOfShares: Optional[Any] = None
    OccrpId: Optional[Any] = None
    Occupation: Optional[Any] = None
    OcId: Optional[Any] = None
    OfficerNumber: Optional[Any] = None
    OffshoreId: Optional[Any] = None
    OpensanctionsId: Optional[Any] = None
    OriginalData: Optional[Any] = None
    OtherAccounts: Optional[Any] = None
    OtherNames: Optional[Any] = None
    OtherNationalities: Optional[Any] = None
    PageTitle: Optional[Any] = None
    PhoneNumbers: Optional[Any] = None
    Place: Optional[Any] = None
    PlaceOfIssue: Optional[Any] = None
    PossiblySensitive: Optional[Any] = None
    Postcode: Optional[Any] = None
    PostsCount: Optional[Any] = None
    Price: Optional[Any] = None
    PrimaryColour: Optional[Any] = None
    Private: Optional[Any] = None
    ProfileUrl: Optional[Any] = None
    ReactCount: Optional[Any] = None
    Region: Optional[Any] = None
    Registration: Optional[Any] = None
    RegistrationCountry: Optional[Any] = None
    RegistrationState: Optional[Any] = None
    RelationshipStatus: Optional[Any] = None
    ReplyToName: Optional[Any] = None
    ReplyToTweetId: Optional[Any] = None
    Retweet: Optional[Any] = None
    RetweetCount: Optional[Any] = None
    RetweetId: Optional[Any] = None
    RetweetUsername: Optional[Any] = None
    ReviewStatus: Optional[Any] = None
    ReviewTime: Optional[Any] = None
    Salutation: Optional[Any] = None
    SavedAt: Optional[Any] = None
    ScreenName: Optional[Any] = None
    SerialNumber: Optional[Any] = None
    ShareCount: Optional[Any] = None
    ShortDomain: Optional[Any] = None
    SicCode: Optional[Any] = None
    Site: Optional[Any] = None
    Source: Optional[Any] = None
    Ssn: Optional[Any] = None
    StartTime: Optional[Any] = None
    Status: Optional[Any] = None
    StatusSince: Optional[Any] = None
    Street1: Optional[Any] = None
    Street2: Optional[Any] = None
    Street3: Optional[Any] = None
    Summary: Optional[Any] = None
    TagLine: Optional[Any] = None
    Tags: Optional[Any] = None
    Text: Optional[Any] = None
    TextSize: Optional[Any] = None
    Timestamp: Optional[Any] = None
    TimeZone: Optional[Any] = None
    Title: Optional[Any] = None
    TloxpId: Optional[Any] = None
    TotalOfficerships: Optional[Any] = None
    TradeDescription: Optional[Any] = None
    TweetsCount: Optional[Any] = None
    Type: Optional[Any] = None
    UpdatedAt: Optional[Any] = None
    UpdatedTime: Optional[Any] = None
    Uri: Optional[Any] = None
    Url: Optional[Any] = None
    Urls: Optional[Any] = None
    Userid: Optional[Any] = None
    UserId: Optional[Any] = None
    UserMentions: Optional[Any] = None
    Username: Optional[Any] = None
    UserName: Optional[Any] = None
    UtcOffset: Optional[Any] = None
    VatNumber: Optional[Any] = None
    Verified: Optional[Any] = None
    VideosCount: Optional[Any] = None
    Vin: Optional[Any] = None
    Websites: Optional[Any] = None
    Work: Optional[Any] = None
    WorldCheckId: Optional[Any] = None
    Worldcompliance: Optional[Any] = None
    Year: Optional[Any] = None


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
