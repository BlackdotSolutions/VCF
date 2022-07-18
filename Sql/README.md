# SQL Adaptor

This repository contains a generic SQL search adaptor for the Videris Connector Framework. It can be deployed as a set of .NET 6.0 binaries or as a Docker container for execution in a host of your choice.

Configuration of the adaptor takes place in two places:

* Environment variables - used to setup how the system executes and consumes the connection information
* Json - a json file is used to specify connection strings and configure searchers and entity types etc.

## Container Configuration (Environment Variables)

The following options are available for configuration of the container and are specified as environment variables for the docker container. How these are set depends on how you are hosting the container - the included deployment examples show how to set them for ECS and Azure Container Apps respectively. 

| Variable                   | Description                                                                                                                                                                                        |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| configuri                  | _(Optional)_ If set then the configuration JSON will be loaded from the specified URI, otherwise it will need to be bundled into the Docker container                                              | 
| azurekeyvaulturi           | _(Optional)_ If set then Azure Key Vault will be used as the secret provider.                                                                                                                      |
| azurekeyvaulttenantid      | _(Optional)_ If set then this is the tenant ID for the service principal used to access the key vault.                                                                                             |
| azurekeyvaultclientid      | _(Optional)_ If set then this service principal will be used for authentication. If not then managed identity will be used.                                                                        |
| azurekeyvaultclientsecret  | _(Optional)_ The corresponding secret for the client ID.                                                                                                                                           |
| awssecretmanager           | _(Optional)_ If set to anything then AWS secret manager will be used                                                                                                                               |
| awssecretmanagerregion     | _(Optional)_ The AWS region the key vault can be found in e.g. eu-west-1.                                                                                                                          |

_(note these are all lower case due to variations in cloud provider naming constraints)_

## Json Configuration

A JSON file is used to provide connection and configuration information for databases. It can be supplied in two ways:

1. As part of the container itself - place a file called config.json alongside the binaries.
2. From a URL - specify the location of the configuration file using the configUri environment variable (if you are using Azure this can be blob storage using a shared access signature, or on AWS an S3 bucket that the Docker container has access to via an IAM role).

A sample config.json file is included in the repository for the AdventureWorks SQL database (you can create one of these in the Azure portal to experiment with).

The JSON file is a set of connections. Each connection will be exposed in Videris as a searcher. A simple example is shown below:

    {
      "connections": [
        {
          "connectionString": "Server=tcp:mysqlserver.database.windows.net,1433;Initial Catalog=sales;Persist Security Info=False;User ID=sqladmin;Password={!dbpassword!};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;",
          "id": "simple",
          "name": "Simple",
          "serverType": "SQLServer",
          "entities": [
            {
              "name": "SalesLT.Customer",
              "title": "LastName",
              "source": "Customers (Individuals)",
              "entityDefinition": {
                "entityType": "EntityPerson",
                "entityAttributes": [
                  { "fromColumn": "FirstName", "toAttribute": "FirstName"},
                  { "fromColumn": "LastName", "toAttribute": "LastName"}
                ]
              }
            }
          ]
        }
      ]
    }

Each connection must have a connection string, a unique ID (within this set of connections), a name, and a database type:

|Property| Description|
|--------|----------------------------------------------------------------------------------------------------------------------------|
|connectionString| The connection to the SQL database - note that secrets can be externalised into an appropriate secret manager (see below). |
|id| Uniquely identifies this connection with this configuration file|
|name| Human readable name for the connection|
|serverType| Currently must be SQLServer (supports on-premise and Azure based SQL Server)|
|entities| A set of entities that can be searched using this connection|

A connection can search one or more entity types with each entity type mapping onto a SQL table or view.

The entities block has the following properties:

|Property|Description|
|--------|-----------|
|name|The name of the table or view to query|
|title|Optional column name (can be an expression) used to generate the title in the search results|
|source|Name of the source|
|searchColumns|The set of columns to be searched and an optional weighting|
|entityDefinition|Maps the results to a Videris entity|

See the sample config.json for the format of the searchColumns and entityDefinition blocks. Valid entity types and toAttribute types are provided at the end of this document.


## Secret Management

Depending on your deployment you may be comfortable with passwords in connection strings or you may prefer to use a secret manager. Their is built in support for both AWS Secret Manager and Azure Key Vault.

To use a secret in a connection string a simple template approach is used to reference secrets. secrets are embedded in a {! !} pair as can be seen in the example below where there is a reference to a secret called _myPassword_.

    Server=aserver;Password={!myPassword!}

Configuring each secret manager is described below. The secret manager to use is auto-detected from the environment settings specified. If an AWS environment variable is specified then AWS will be used, if an Azure environment variable is specified then Azure Key Vault will be used. If both are specified AWS will be used.

#### AWS Secret Manager

Your docker container will need running under an IAM account with permissions to read secrets from the secret manager or have access granted to each individual secret (the recommended approach). If no specific configuration is required then simply set the _awsSecretManager_ to any value (e.g. 1 or true).

You can connect to a Secret Manager in a specific region by using the _awsSecretManagerRegion_ setting, for example:

    awsSecretManagerRegion=eu-west-1

If you set the region you do not need to specify _awsSecretManager_.

#### Azure Key Vault

This can be used with either a service principal or a managed identity. In both cases the URI of the key vault needs specifying:

    azureKeyVaultUri=https://mydemokeyvault.vault.azure.net/

To use with a service principal set up as per [these instructions](https://docs.microsoft.com/en-us/dotnet/api/overview/azure/security.keyvault.secrets-readme?view=azure-dotnet). Then set the service principal credentials as shown below:

    azureKeyVaultTenantId=<your_tenant_id>
    azureKeyVaultClientId=<your_client_id>
    azureKeyVaultClientSecret=<your_client_secret>

To use with managed identity no configuration is required beyond setting the URI and configuring the managed identity on the container host and key vault - how you do this depends on how you are running the docker container, please see Azure documentation.

## Deployment

The adaptor is a simple ASP.Net Core application (.NET 6) and can be hosted in any environment capable of doing so. However it is delivered with a Dockerfile for easy deployment as a container. This repository includes two sample approaches for deploying into AWS and Azure.

Note that the two included samples deploy onto a public endpoint. In reality you are likely to want to deploy onto a private endpoint / subnet and the scripts should be modified to meet your requirements in this regard.

### Deploying into IIS

The application is a .NET 6.0 app which can be deployed into IIS per [these instructions](https://docs.microsoft.com/en-us/aspnet/core/host-and-deploy/iis/?view=aspnetcore-6.0).

### Deploying into AWS

This method uses the [AWS CDK](https://aws.amazon.com/cdk/) to create an ECS service (and associated resources) that hosts the Docker container as a task. To get started you will need to configure the [AWS CLI](https://aws.amazon.com/cli/) and the [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html). You must have run _aws configure_ before you attempt to deploy the stack.

Configuration options are supplied to the CDK through environment variables that can either be set in your shell or in a .env file located in the _AwsEcs.Deploy folder_. These environment variables are as follows:

| Variable       | Description                                                                                                                                                                                                                                                                                                                    |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ncsa_configuri | If set then this is the location of the configuration document (see Json Configuration above). It needs to be accessible to the machine and in the shell the CDK is being run as it will be scanned for any secret tokens. If this is not specified then a config.json file will be looked for in the NoCodeSqlAdaptor folder. |
| ncsa_domain    | The domain the endpoint should be exposed on. Optional but required if you wish to use https.                                                                                                                                                                                                                                  |
| ncsa_subdomain | Required if ncsa_domain is set.                                                                                                                                                                                                                                                                                                |
| ncsa_hostedzone|The name of the Hosted Zone the domain is registered in in Route 53. If not specified then the name will be assumed to be the domain name.|

Note that if you don't specify ncsa_configuri then you must complete the config.json file that can be found in the NoCodeSqlAdaptor folder - this file is bundled inside the Docker container and will be used if no external config is supplied.

To expose the adaptor on https then a domain name must be registered within Route 53 and the _ncsa_domain_ and _ncsa_subdomain_ variables set.

If you have any tokenized secrets in your config.json then they will be extracted and the ECS task role will granted read rights to them in secret manager by this deployment. They must therefore exist prior to deployment of the CDK stack.

When you are ready to deploy the stack simply go to the AwsEcs.Deploy folder and enter the following in your shell:

    cdk deploy

You will find the public endpoint in the output of the stack. 

### Deploying into Azure

This method uses [Farmer](https://compositionalit.github.io/farmer/) to create an Azure Container Apps environment that hosts the Docker container. To get started you will require the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) to be installed and you will need to be logged in and have selected your subscription.

## Enhancements

Things that could be added and in some cases for which some of the infrastructure is in place:

* Postgres support
* SQL Server free text support
* Use a table/views GUID ID as the Videris ID if it is of type GUID

## Valid entity types

* EntityGenericOnlineProfile
* EntityAddress
* EntityAsset
* EntityBusiness
* EntityCar
* EntityCollege
* EntityDarkWebPage
* EntityDirectorRecord
* EntityDocument
* EntityDomain
* EntityEbayProfile
* EntityEmail
* EntityEvent
* EntityFacebookEvent
* EntityFacebookGroup
* EntityFacebookListing
* EntityFacebookPage
* EntityFacebookPhoto
* EntityFacebookPost
* EntityFacebookProfile
* EntityFacebookVideo
* EntityFlickrGroup
* EntityFlickrProfile
* EntityGabGroup
* EntityGabPost
* EntityGabProfile
* EntityGooglePlusProfile
* EntityGroup
* EntityIdentityDocument
* EntityImage
* EntityImeiDevice
* EntityInstagramLocation
* EntityInstagramPost
* EntityInstagramProfile
* EntityIpAddress
* EntityJustgivingProfile
* EntityLabel
* EntityLinkedinGroup
* EntityLinkedinOrganisation
* EntityLinkedinProfile
* EntityMailServer
* EntityNameServer
* EntityNote
* EntityOdnoklassnikiProfile
* EntityOfficerRecord
* EntityOnlineIdentity
* EntityOrganisation
* EntityParlerPost
* EntityParlerProfile
* EntityPerson
* EntityPhoneNumber
* EntityPhrase
* EntityPinterestProfile
* EntityPlane
* EntityPosting
* EntityProduct
* EntityShip
* EntitySoundcloudProfile
* EntityTiktokProfile
* EntityTripadvisorProfile
* EntityTweet
* EntityTwitterProfile
* EntityUrlInfo
* EntityVkontakteCommunity
* EntityVkontaktePost
* EntityVkontakteProfile
* EntityWebPage
* EntityWikipediaArticle
* EntityWikipediaProfile
* EntityYoutubeProfile
* EntityYoutubeVideo
* RelationshipAction
* RelationshipAlias
* RelationshipAttended
* RelationshipContactDetail
* RelationshipEmployedAt
* RelationshipFamilyMember
* RelationshipHas
* RelationshipHosted
* RelationshipIdentical
* RelationshipInOnlineGroup
* RelationshipLinksTo
* RelationshipLocation
* RelationshipMet
* RelationshipNameserver
* RelationshipNotSimilar
* RelationshipOfficership
* RelationshipOnlineAlsoViewed
* RelationshipOnlineCommented
* RelationshipOnlineEndorsement
* RelationshipOnlineFollows
* RelationshipOnlineFriends
* RelationshipOnlineLikes
* RelationshipOnlinePosted
* RelationshipOnlineProfile
* RelationshipOnlineProfileImage
* RelationshipOnlineRecommendation
* RelationshipOnlineShares
* RelationshipOnlineTagged
* RelationshipOwns
* RelationshipPhoneCall
* RelationshipRegistrant
* RelationshipRelationship
* RelationshipShareholding
* RelationshipSimilar
* RelationshipSourceLink
* SourceHtmlDocument
* SourceHtmlLog
* SourceJsonDocument
* SourceRdfDocument
* SourceSource
* SourceTextFile
* SourceXmlDocument

## Valid toAttribute types

The following values can be used in the toAttribute property when entity mapping.

* None
* FromId
* ToId
* Address
* Album
* AlexaRank
* AlternateName
* Annotator1Imageuri
* Apn
* AreaCode
* Bio
* Biography
* Birthday
* Brand
* BvdId
* CallSign
* Cancelled
* Caption
* Category
* Charges
* City
* Closed
* Collectionid
* Colour
* CommentCount
* Comments
* CompaniesHouseId
* CompanyNumber
* CompanySize
* Compliance
* Confidence
* Connections
* Content
* ContributorsEnabled
* Coordinates
* CorrectedNumber
* Count
* Country
* CountryCode
* CreatedAt
* CreatedDate
* CreatedTime
* Data
* Date
* DateOfDeath
* DateOfIssue
* Deactivated
* Description
* DescriptionText
* Digits
* Direction
* Disqualifications
* Dob
* DocumentId
* DocumentNumber
* DocumentType
* Domain
* DomainName
* Duns
* Education
* EmailAddress
* EmailAddresses
* Encoding
* EndTime
* FamilyMembers
* Favorited
* FavouritesCount
* FilingNumber
* FirstName
* FollowersCount
* FollowingCount
* Format
* FormattedNumber
* FriendCount
* FullAddress
* FullUrl
* Gender
* GeoEnabled
* Groups
* Hashtags
* HeartsCount
* HomeTown
* Html
* Id
* Image
* Imageuri
* Imei
* ImoNumber
* IncorporationDate
* Industry
* InsolvencyHistory
* Interests
* IpAddress
* IsCompany
* JobTitle
* Kind
* Language
* Languages
* LastName
* LastSeen
* LikeCount
* Liquidated
* ListedCount
* LiveListing
* Locale
* LocalName
* LocalNumber
* LocalPart
* Location
* Make
* Members
* MetaDescription
* MetaKeywords
* Model
* Name
* Nationality
* NationalNumber
* Network
* Number
* NumberOfShares
* OccrpId
* Occupation
* OcId
* OfficerNumber
* OffshoreId
* OriginalData
* OtherAccounts
* OtherNames
* PageTitle
* PhoneNumbers
* Place
* PlaceOfIssue
* PossiblySensitive
* Postcode
* PostsCount
* Price
* PrimaryColour
* Private
* ProfileUrl
* ReactCount
* Region
* Registration
* RegistrationCountry
* RegistrationState
* RelationshipStatus
* ReplyToName
* ReplyToTweetId
* Retweet
* RetweetCount
* RetweetId
* RetweetUsername
* ReviewStatus
* ReviewTime
* Salutation
* SavedAt
* ScreenName
* SerialNumber
* ShareCount
* ShortDomain
* SicCode
* Site
* Source
* Ssn
* StartTime
* Status
* StatusSince
* Street1
* Street2
* Street3
* Summary
* TagLine
* Tags
* Text
* TextSize
* Timestamp
* TimeZone
* Title
* TloxpId
* TotalOfficerships
* TradeDescription
* TweetsCount
* Type
* UpdatedAt
* UpdatedTime
* Uri
* Url
* Urls
* Userid
* UserId
* UserMentions
* Username
* UserName
* UtcOffset
* VatNumber
* Verified
* VideosCount
* Vin
* Websites
* Work
* WorldCheckId
* Worldcompliance
* Year
