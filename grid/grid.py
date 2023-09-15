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

import requests

from vcf import create_relationship


GRID_API_USERNAME = os.getenv('GRID_API_USERNAME')
GRID_API_PASSWORD = os.getenv('GRID_API_PASSWORD')
GRID_TOKEN_FILE_PATH = (os.getenv('GRID_TOKEN_FILE_PATH') or 'grid-token.json')
GRID_API_BASE_URL = 'https://service.rdc.eu.com/api/grid-service/v2/'


def log(*message):
    print(datetime.now().isoformat(), *message)


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
                return self.token
        log('Unable to login:', response.text)

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
        log('Token refetching failed, error response:', response.text)
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
        log('Request:', method, 'Url:', self.url(_url))
        response = getattr(self.client, method.lower())(self.url(_url), **kwargs)
        if response.status_code in (401, 403,):
            log('Got', response.status_code, 'response. Refetching token')
            self.refetch_token()
            self.make_client()
            response = getattr(self.client, method.lower())(self.url(_url), **kwargs)
        if not response.ok:
            log('Got error response', response, ':', response.content)

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
        query = query.strip()
        query_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, query))
        company_query = {
            'portfolioMonitoring': 'false',
            'searchActionIfDuplicate': 'SEARCH',
            'loadOnly': 'false',
            'globalsearch': 'false',
            'tracking': query_uuid,
            'gridOrgPartyInfo': {
                'gridOrgData': {
                    'orgName': {
                        'name': query,
                    },
                },
            },
        }
        response = api.make_request('post', 'inquiry', json=company_query)
        if not response.ok:
            return {'error': [{'message': 'Error response from Grid API.'}]}

        alerts_list = response.json().get('data', {}).get('alerts', [])
        if not alerts_list:
            return {'searchResults': []}

        company_list = alerts_list[0].get('gridAlertInfo', {}).get('alerts', {}).get('nonReviewedAlertEntity') or []
    except:
        traceback.print_exc()
        return {'error': [{'message': 'Error querying the Grid API.'}]}

    for company in company_list:
        company_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, company['sysId']))

        # Create search result
        # Address
        possible_addresses = company.get('postAddr') or []
        address_entities = []
        for company_address_index, company_address in enumerate(possible_addresses):
            street1 = (company_address.get('addr1') or '').strip()
            city = (company_address.get('city') or '').strip()
            region = (company_address.get('stateProv') or '').strip()
            postcode = (company_address.get('postalCode') or '').strip()
            country = (company_address.get('countryCode', {}).get('countryCodeValue') or '').strip()

            full_address = ', '.join([
                _fragment for _fragment in [
                    street1, city, region, postcode, country,
                ] if _fragment
            ]) or '-'

            address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(
                # Make sure address has a reproducible uuid that's unique (i.e. doesn't depend on null values
                # in case record is not present).
                full_address or
                ('address-' + str(company_address_index) + '-' + company_uuid)
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
                }
            }
            address_entities.append(address_entity)

        # Riskography
        riskcographies = []
        riskids = []
        for _attr in (company.get('attribute') or []):
            if _attr.get('attCode') == 'RID' and _attr.get('attVal'):
                riskids.append(_attr['attVal'])
            elif _attr.get('attCode') == 'RGP' and _attr.get('attVal'):
                riskcographies.append(_attr['attVal'])
        riskids_display = ', '.join(riskids)
        riskcographies_display = ', '.join(riskcographies)

        # Summary
        summary_chunks = []
        if riskids_display:
            summary_chunks.append('Risk ID: ' + riskids_display)
        if riskcographies_display:
            summary_chunks.append('Riskography: ' + riskcographies_display)

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': company['entityName'],
            'subTitle': '',
            'summary': ' | '.join(summary_chunks),
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
        for address_entity in address_entities:
            result['entities'].append(address_entity)
            result['entities'].append(create_relationship(company_uuid, address_entity['id'], 'Company Address'))

        # Relationship: Persons
        for relation in company.get('relations') or []:
            if relation.get('relTyp') in ('EMPLOYEE', 'ASSOCIATE',):
                # Construct First Name and Last Name
                person_name_words = (relation['entityName'] or '').split(' ')
                relation_entity = {
                    'id': str(uuid.uuid4()).upper(),
                    'type': 'EntityPerson',
                    'attributes': {
                        'FirstName': (person_name_words[0] if person_name_words else '').strip(),
                        'LastName': (' '.join(person_name_words[1:]) if person_name_words else '').strip(),
                        'JobTitle': relation.get('relTyp') or '',
                    }
                }
                result['entities'].append(relation_entity)
                result['entities'].append(create_relationship(company_uuid, relation_entity['id'], 'Person'))

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
        query = query.strip()
        query_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, query))
        people_query = {
            'portfolioMonitoring': 'false',
            'searchActionIfDuplicate': 'SEARCH',
            'loadOnly': 'false',
            'globalsearch': 'false',
            'tracking': query_uuid,
            'gridPersonPartyInfo': {
                'gridPersonData': {
                    'personName': {
                        'fullName': query,
                    },
                },
            },
        }
        response = api.make_request('post', 'inquiry', json=people_query)
        if not response.ok:
            return {'error': [{'message': 'Error response from Grid API.'}]}

        alerts_list = response.json().get('data', {}).get('alerts', [])
        if not alerts_list:
            return {'searchResults': []}

        entities_list = alerts_list[0].get('gridAlertInfo', {}).get('alerts', {}).get('nonReviewedAlertEntity') or []
    except:
        traceback.print_exc()
        return {'error': [{'message': 'Error querying the Grid API.'}]}

    for entity in entities_list:
        entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, entity['sysId']))

        # Create search result
        # Address
        nationality = ''
        possible_addresses = entity.get('postAddr') or []
        address_entities = []
        for entity_address_index, entity_address in enumerate(possible_addresses):
            street1 = (entity_address.get('addr1') or '').strip()
            city = (entity_address.get('city') or '').strip()
            region = (entity_address.get('stateProv') or '').strip()
            postcode = (entity_address.get('postalCode') or '').strip()
            country = (entity_address.get('countryCode', {}).get('countryCodeValue') or '').strip()

            full_address = ', '.join([
                _fragment for _fragment in [
                    street1, city, region, postcode, country,
                ] if _fragment
            ]) or '-'

            address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(
                # Make sure address has a reproducible uuid that's unique (i.e. doesn't depend on null values
                # in case record is not present).
                full_address or
                ('address-' + str(entity_address_index) + '-' + entity_uuid)
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
                }
            }
            address_entities.append(address_entity)

            if entity_address.get('locatorTyp') == 'BIRTH':
                nationality = country

        # Construct First Name and Last Name
        person_name_words = (entity['entityName'] or '').split(' ')

        # Construct Date of Birth
        possible_dobs = entity.get('birthDt') or []
        dob = ''
        for possible_dob in possible_dobs:
            if possible_dob.strip():
                dob = possible_dob
                break

        # Riskography
        riskcographies = []
        riskids = []
        for _attr in (entity.get('attribute') or []):
            if _attr.get('attCode') == 'RID' and _attr.get('attVal'):
                riskids.append(_attr['attVal'])
            elif _attr.get('attCode') == 'RGP' and _attr.get('attVal'):
                riskcographies.append(_attr['attVal'])
        riskids_display = ', '.join(riskids)
        riskcographies_display = ', '.join(riskcographies)

        # Summary
        summary_chunks = []
        if riskids_display:
            summary_chunks.append('Risk ID: ' + riskids_display)
        if riskcographies_display:
            summary_chunks.append('Riskography: ' + riskcographies_display)

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': entity['entityName'],
            'subTitle': '',
            'summary': ' | '.join(summary_chunks),
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
        for relation in entity.get('relations') or []:
            if relation.get('relTyp') in ('EMPLOYEE', 'ASSOCIATE',):
                relation_entity = {
                    'id': str(uuid.uuid4()).upper(),
                    'type': 'EntityBusiness',
                    'attributes': {
                        'Name': relation.get('entityName') or '',
                        'LocalName': relation.get('entityName') or '',
                        'JobTitle': relation.get('relTyp') or '',
                    }
                }
                result['entities'].append(relation_entity)
                result['entities'].append(create_relationship(entity_uuid, relation_entity['id'], 'Company'))

        # Relationship: Events
        for event in entity.get('events') or []:
            _category_code = event.get('category', {}).get('categoryCode') or ''
            _category = event.get('category', {}).get('categoryDesc') or ''
            if _category_code:
                _category = _category + ' (' + _category_code + ')'
            _category = _category.strip()

            if event.get('category', {}).get('categoryCode') == 'WLT':
                event_entity = {
                    'id': str(uuid.uuid4()).upper(),
                    'type': 'EntityOrganisation',
                    'attributes': {
                        'Name': event.get('source', {}).get('sourceName') or '',
                        'Category': _category,
                    }
                }
                result['entities'].append(event_entity)
                result['entities'].append(create_relationship(entity_uuid, event_entity['id'], 'Sanctioned by'))
            else:
                _description = (event.get('source', {}).get('headline') or '') + '\n Category: ' + event.get('subCategory', {}).get('categoryDesc')
                event_entity = {
                    'id': str(uuid.uuid4()).upper(),
                    'type': 'EntityEvent',
                    'attributes': {
                        'Title': event.get('eventDesc') or '',
                        'Date': event.get('eventDt') or '',
                        'Url': event.get('source', {}).get('sourceURL') or '',
                        'Description': _description.strip() or '',
                        'Category': _category,
                    }
                }
                result['entities'].append(event_entity)
                result['entities'].append(create_relationship(entity_uuid, event_entity['id'], ''))

        # Relationship: Attributes
        for attribute in entity.get('attributes') or []:
            if attribute.get('code') != 'URL':
                attribute_entity = {
                    'id': str(uuid.uuid4()).upper(),
                    'type': 'EntityNote',
                    'attributes': {
                        'Text': attribute.get('value') or '',
                    }
                }
                result['entities'].append(attribute_entity)
                result['entities'].append(create_relationship(entity_uuid, attribute_entity['id'], ''))

        search_results.append(result)
        if len(search_results) >= max_results:
            break

    return {'searchResults': search_results}
