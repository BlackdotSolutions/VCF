"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import json
import os
import traceback
import uuid
from datetime import datetime
import logging

import requests

from vcf import create_relationship

logger = logging.getLogger("gridlogger")
handler = logging.FileHandler('grid.log')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


GRID_API_USERNAME = os.getenv('GRID_API_USERNAME')
GRID_API_PASSWORD = os.getenv('GRID_API_PASSWORD')
GRID_TOKEN_FILE_PATH = (os.getenv('GRID_TOKEN_FILE_PATH') or 'grid-token.json')
GRID_API_BASE_URL = 'https://service.rdc.eu.com/api/grid-service/v2/'


def log(message):
#    print(datetime.now().isoformat(), message)
    logger.warning(message)

def sentence(input:str = ""):
    return input.replace("_"," ").capitalize()


# ============================ Grid API Client ===========================
class GridAPIClient:

    username = GRID_API_USERNAME
    password = GRID_API_PASSWORD
    token = ''
    client = None

    def login(self):
        log('Logging in')
        response = requests.post('https://service.rdc.eu.com/oauth/login', json={
            'userId': self.username,
            'password': self.password,
        }, timeout=5.0)
        if response.ok:
            if response.json()['success']:
                log('Successfully logged in')
                self.token = response.json()['data']['access_token']
                with open(GRID_TOKEN_FILE_PATH, 'w') as token_file:
                    json.dump(response.json(), token_file)
                return response.json()
            log('Unable to login: ' + response.json())

    def refetch_token(self):
        log('Refetching token')
        token_info = self.get_token_info()
        response = requests.post('https://service.rdc.eu.com/oauth/token', headers={
            'Content-Type': 'application/json',
            'Authorization': self.token,
            'Refresh-Token': token_info.get('data', {}).get('refresh_token'),
        }, timeout=5.0)
        if response.ok:
            log('Successfully refetched token')
            self.token = response.json()['data']['access_token']
            with open(GRID_TOKEN_FILE_PATH, 'w') as token_file:
                json.dump(response.json(), token_file)
            return self.token

        # token refresh failed, try to login again
        return self.login()

    def get_token_info(self):
        log('Reading token info from file')
        token_info = {}
        try:
            with open(GRID_TOKEN_FILE_PATH, 'r') as token_file:
                token_info = json.load(token_file)
                if not token_info:
                    raise Exception('Empty token file')
        except:
            # file not present, could be the first call
            log('Unable to read token info from file, trying to login')
            return self.login()
        return token_info

    def get_token(self):
        return self.get_token_info()['data']['access_token']

    def make_client(self):
        log('Make API client')
        self.token = self.get_token()
        self.client = requests.Session()
        self.client.headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
        }
        return self.client

    def url(self, _url):
        return GRID_API_BASE_URL + _url

    def make_request(self, method, _url, **kwargs):
        log(f'Request: {method} Url: {self.url(_url)}')
        response = getattr(self.client, method.lower())(self.url(_url), **kwargs)

        if response.status_code in (401, 403,):
            log(f'Got {response.status_code} response. Refetching token')
            self.refetch_token()
            self.make_client()
            response = getattr(self.client, method.lower())(self.url(_url), **kwargs)

        if not response.ok:
            log(f'Got error response {response}: {response.content}')
        else:
            log(f"Successful response: {response}: {response.content}")

        return response


# ============================ Grid functions ============================
async def get_grid_company(query: str, max_results: int = 50):
    search_results = []

    try:
        api = GridAPIClient()
        api.make_client()
    except:
        return {'error': [{'message': 'Error establishing a connection with the Grid API.'}]}

    try:
        response = api.make_request('post', 'entity/searches', json={
            "criteria": [
                {
                    "name": query,
                    "entityTyp": "O"
                }
            ]
        })
        if not response.ok:
            return {'error': [{'message': 'Error response from Grid API.'}]}
        company_list = response.json().get('data') or []
    except:
        traceback.print_exc()
        return {'error': [{'message': 'Error querying the Grid API.'}]}
    # log(response.json())
    for company in company_list:
        company_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, company['id']))

        # Create search result
        # Address
        possible_addresses = company.get('addresses') or []
        address_entities = []
        count = 0
        for company_address in possible_addresses:
            if count < 10:
                street1 = (company_address.get('addr1') or '').strip()
                city = (company_address.get('city') or '').strip()
                region = (company_address.get('stateProv') or '').strip()
                postcode = (company_address.get('postalCode') or '').strip()
                country = (company_address.get('countryCode') or '').strip()

                full_address = ', '.join([
                    _fragment for _fragment in [
                        street1, city, region, postcode, country,
                    ] if _fragment
                ]) or None

                address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(
                    # Make sure address has a reproducible uuid that's unique (i.e. doesn't depend on null values
                    # in case record is not present).
                    full_address
                )))
                address_entity = {
                    'id': address_uuid,
                    'type': 'EntityAddress',
                    'attributes': {
                        'Street1': street1,
                        'City': city,
                        'Region': region,
                        'Postcode': postcode,
                        'Country': country,
                        'Nationality': country,
                        'FullAddress': full_address
                    }
                }
                address_entities.append(address_entity)
                # log(str(address_entity))
            else:
                break

            count += 1

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': company['entityName'],
            'subTitle': '',
            'summary': '',
            'source': 'Grid API',
            'url': company['rdcURL'],
            'entities': [
                {
                    'id': company_uuid,
                    'type': 'EntityBusiness',
                    'attributes': {
                        'Name': company['entityName'] or '',
                        'LocalName': company['entityName'] or '',
                        'Description': '',
                        'WorldCompliance': True,
                    }
                }
            ]
        }

        # Relationship: Address
        for address_entity in address_entities:  # VCF truncates the response beyond a certain size so restrict each result to containing a max of 10 addresses
            result['entities'].append(address_entity)
            result['entities'].append(create_relationship(company_uuid, address_entity['id'], 'Company Address'))

        # Relationship: Persons
        count = 0
        for relation in company.get('relations') or []:
            if count < 10:
                relType = relation.get('relTyp') or ""
                if relType in ['EMPLOYEE', 'ASSOCIATE']:
                    # Construct First Name and Last Name
                    person_name_words = (relation['entityName'] or '').split(' ')
                    relation_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityPerson',
                        'attributes': {
                            'FirstName': (person_name_words[0] if person_name_words else '').strip(),
                            'LastName': (' '.join(person_name_words[1:]) if person_name_words else '').strip()
                        }
                    }
                    result['entities'].append(relation_entity)
                    result['entities'].append(create_relationship(company_uuid, relation_entity['id'], sentence(relType)))
            else:
                break

            count += 1

        # Relationship: Events
        count = 0
        # VCF truncates the response beyond a certain size so restrict each result to containing a max of 10 events
        for event in company.get('events') or []:
            if count < 10:
                if event.get('category', {}).get('categoryCode') == 'WLT':
                    event_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityOrganisation',
                        'attributes': {
                            'Name': event.get('source', {}).get('sourceName') or '',
                        }
                    }
                    result['entities'].append(event_entity)
                    result['entities'].append(create_relationship(company_uuid, event_entity['id'], 'Sanctioned by'))
                else:
                    _description = (event.get('source', {}).get('headline') or '') + \
                        '\n Category: ' + event.get('subCategory', {}).get('categoryDesc')
                    event_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityEvent',
                        'attributes': {
                            'Title': event.get('eventDesc') or '',
                            'Date': event.get('eventDt')+'T00:00:00.000+0000' or '',
                            'Url': event.get('source', {}).get('sourceURL') or '',
                            'Description': _description.strip() or '',
                        }
                    }
                    result['entities'].append(event_entity)
                    result['entities'].append(create_relationship(company_uuid, event_entity['id'], ''))

            else:
                break

            count += 1

        search_results.append(result)
        if len(search_results) >= max_results:
            break

    return {'searchResults': search_results}


async def get_grid_people(query: str, max_results: int = 50):
    search_results = []

    try:
        api = GridAPIClient()
        api.make_client()
    except:
        return {'error': [{'message': 'Error establishing a connection with the Grid API.'}]}

    try:
        response = api.make_request('post', 'entity/searches', json={
            "criteria": [
                {
                    "name": query,
                    "entityTyp": "P"
                }
            ]
        })
        if not response.ok:
            return {'error': [{'message': 'Error response from Grid API.'}]}
        entities_list = response.json().get('data') or []
    except:
        traceback.print_exc()
        return {'error': [{'message': 'Error querying the Grid API.'}]}
    # log(response.json())
    for entity in entities_list:
        entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, entity['id']))

        # Create search result
        # Address
        nationality = ''
        # VCF truncates the response beyond a certain size so restrict each result to containing a max of 10 addresses
        possible_addresses = entity.get('addresses') or []
        address_entities = []
        count = 0
        for entity_address in possible_addresses:
            if count < 10:
                street1 = (entity_address.get('addr1') or '').strip()
                city = (entity_address.get('city') or '').strip()
                region = (entity_address.get('stateProv') or '').strip()
                postcode = (entity_address.get('postalCode') or '').strip()
                country = (entity_address.get('countryCode') or '').strip()

                full_address = ', '.join([
                    _fragment for _fragment in [
                        street1, city, region, postcode, country,
                    ] if _fragment
                ]) or None
                if full_address:
                    address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(
                        # Make sure address has a reproducible uuid that's unique (i.e. doesn't depend on null values
                        # in case record is not present).
                        full_address
                    )))
                    address_entity = {
                        'id': address_uuid,
                        'type': 'EntityAddress',
                        'attributes': {
                            'Street1': street1,
                            'City': city,
                            'Region': region,
                            'Postcode': postcode,
                            'Country': country,
                            'Nationality': country,
                            'FullAddress': full_address
                        }
                    }
                    address_entities.append(address_entity)

                    if entity_address.get('locatorTyp') == 'BIRTH':
                        nationality = entity_address.get('countryCode') or ''

                    count += 1
            else:
                break



        # Construct First Name and Last Name
        person_name_words = (entity['entityName'] or '').split(' ')

        # Construct Date of Birth
        possible_dobs = entity.get('birthDt') or []
        dob = ''
        for possible_dob in possible_dobs:
            if possible_dob.strip():
                dob = possible_dob
                break

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': entity['entityName'],
            'subTitle': '',
            'summary': '',
            'source': 'Grid API',
            'url': entity['rdcURL'],
            'entities': [
                {
                    'id': entity_uuid,
                    'type': 'EntityPerson',
                    'attributes': {
                        'FirstName': (person_name_words[0] if person_name_words else '').strip(),
                        'LastName': (' '.join(person_name_words[1:]) if person_name_words else '').strip(),
                        'Dob': dob or '',
                        'Nationality': nationality,
                        'Compliance': True,
                    }
                }
            ]
        }

        # Relationship: Address
        for address_entity in address_entities:
            result['entities'].append(address_entity)
            result['entities'].append(create_relationship(entity_uuid, address_entity['id'], 'Person Address'))

        # Relationship: Company
        count = 0
        for relation in entity.get('relations') or []:
            if count < 10:
                relType = relation.get('relTyp') or ""

                if relType in ['EMPLOYEE', 'ASSOCIATE']:
                    relation_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityBusiness',
                        'attributes': {
                            'Name': relation.get('entityName') or '',
                            'LocalName': relation.get('entityName') or ''
                        }
                    }
                    result['entities'].append(relation_entity)
                    result['entities'].append(create_relationship(entity_uuid, relation_entity['id'], sentence(relType)))
                else:
                    # Construct First Name and Last Name
                    person_name_words = (relation['entityName'] or '').split(' ')
                    relation_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityPerson',
                        'attributes': {
                            'FirstName': (person_name_words[0] if person_name_words else '').strip(),
                            'LastName': (' '.join(person_name_words[1:]) if person_name_words else '').strip(),
                        }
                    }
                    result['entities'].append(relation_entity)
                    result['entities'].append(create_relationship(entity_uuid, relation_entity['id'], sentence(relType)))
            else:
                break
            count += 1

        # Relationship: Events
        # VCF truncates the response beyond a certain size so restrict each result to containing a max of 10 events
        count = 0
        for event in entity.get('events') or []:
            if count < 10:
                if event.get('category', {}).get('categoryCode') == 'WLT':
                    event_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityOrganisation',
                        'attributes': {
                            'Name': event.get('source', {}).get('sourceName') or '',
                        }
                    }
                    result['entities'].append(event_entity)
                    result['entities'].append(create_relationship(entity_uuid, event_entity['id'], 'Sanctioned by'))
                else:
                    _description = (event.get('source', {}).get('headline') or '') + \
                        '\n Category: ' + event.get('subCategory', {}).get('categoryDesc')
                    event_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityEvent',
                        'attributes': {
                            'Title': event.get('eventDesc') or '',
                            'Date': event.get('eventDt') or '',
                            'Url': event.get('source', {}).get('sourceURL') or '',
                            'Description': _description.strip() or '',
                        }
                    }
                    result['entities'].append(event_entity)
                    result['entities'].append(create_relationship(entity_uuid, event_entity['id'], ''))
            else:
                break
            count += 1

        # Relationship: Attributes
        # VCF truncates the response beyond a certain size so restrict each result to containing a max of 10 attributes
        count = 0
        for attribute in entity.get('attributes') or []:
            if count < 10:
                # Ideally SEX would populate a gender attribute but can live without
                if attribute.get('code') not in ['URL', 'SEX']:
                    attribute_entity = {
                        'id': str(uuid.uuid4()).upper(),
                        'type': 'EntityNote',
                        'attributes': {
                            'Description': attribute.get('value') or '',  # Seems like `Text` is not accepted by Videris
                        }
                    }
                    result['entities'].append(attribute_entity)
                    result['entities'].append(create_relationship(entity_uuid, attribute_entity['id'], ''))
            else:
                break
            count += 1
        search_results.append(result)
        if len(search_results) >= max_results:
            break

    return {'searchResults': search_results}
