"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import os
import uuid

import requests

from vcf import create_relationship


SAYARI_CLIENT_ID = os.getenv('SAYARI_CLIENT_ID')
SAYARI_CLIENT_SECRET = os.getenv('SAYARI_CLIENT_SECRET')


SAYARI_BASE_URL = 'https://api.sayari.com/'


# ============================ Sayari API Client ===========================
class SayariAPIClient:

    client_id = SAYARI_CLIENT_ID
    client_secret = SAYARI_CLIENT_SECRET
    token = ''
    client = None

    def fetch_token(self):
        response = requests.post('https://api.sayari.com/oauth/token', json={
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'audience': 'sayari.com',
            'grant_type': 'client_credentials',
        }, timeout=5.0)
        if response.ok:
            self.token = response.json()['access_token']
            return self.token

    def make_client(self):
        self.client = requests.Session()
        self.client.headers = {
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json',
        }
        return self.client

    def url(self, _url):
        return SAYARI_BASE_URL + _url


# ============================ Sayari functions ============================
async def get_sayari_company(query: str, max_results: int = 50):
    search_results = []

    try:
        api = SayariAPIClient()
        api.fetch_token()
        api.make_client()
    except:
        return {'error': [{'message': 'Error establishing a connection with the Sayari API.'}]}

    try:
        response = api.client.get(api.url('search/entity'), params={
            'limit': max_results,
            'q': query,
            'filters': 'entity_type=company'
        })
        if not response.ok:
            return {'error': [{'message': 'Error response from Sayari API.'}]}
        company_list = response.json().get('data') or []
    except:
        return {'error': [{'message': 'Error querying the Sayari API.'}]}

    for listed_company in company_list:
        if listed_company['type'] != 'company':
            # In the company searcher, only return company, and not people etc.
            continue

        try:
            response = api.client.get(api.url(listed_company['entity_url']))
            if not response.ok:
                print('Error fetching company. Returning partial result.', listed_company['url'], response.text)
                return search_results
            company = response.json()
        except:
            print('Error fetching company. Returning partial result.', listed_company['url'], response.text)
            return search_results

        company_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, company['id']))

        # Create search result
        company_status = 'Inactive' if company.get('closed') else 'Active'
        countries_list = ', '.join(company.get('countries') or [])

        # Risk score
        pep_sanction_risk_info_points = []
        risk_value = company.get('risk', {}).get('cpi_score', {}).get('value') or ''
        if risk_value:
            pep_sanction_risk_info_points = [f'Risk Score: {risk_value}']
            if company['sanctioned']:
                pep_sanction_risk_info_points.append('Sanctioned')
            if company['pep']:
                pep_sanction_risk_info_points.append('PEP')
        pep_sanction_risk_info = ' - '.join(pep_sanction_risk_info_points)

        # Incorporation / registration date
        incorporation_date = registration_date = None
        for _status in company.get('attributes', {}).get('status', {}).get('data', []):
            _property = _status.get('properties') or {}
            _property_type = ((_property.get('value') or _property.get('text')) or '').strip().lower() or None
            _property_value = ((_property.get('date') or _property.get('from_date')) or '').strip().lower() or None
            if _property_type == 'incorporated':
                incorporation_date = _property_value
            elif _property_type == 'registered':
                registration_date = _property_value

        # Company number (ID number) and VAT number
        vat_number = uk_company_number = ''
        company_numbers = set()
        for _identifier in company.get('identifiers') or []:
            _should_consider_identifier = (
                _identifier.get('value') and
                _identifier.get('label') and
                (_identifier.get('type') or '').lower() not in ('', 'unknown',)
            )
            if _should_consider_identifier:
                _company_number = f'{_identifier["value"]} ({_identifier["label"].replace("_", " ").upper()})'
                company_numbers.add(_company_number)
                if _identifier['type'] == 'gbr_vat_no':
                    vat_number = _identifier['value']
                if _identifier['type'] == 'uk_company_number':
                    uk_company_number = _identifier['value']

        # SIC code
        sic_code = ''
        for _purpose in company.get('attributes', {}).get('business_purpose', {}).get('data', []):
            if (_purpose.get('properties', {}).get('standard') or '').lower() == 'sic':
                sic_code = _purpose.get('properties', {}).get('code') or ''
                break

        # Registration country
        country_data = {}
        for _country_data_item in company.get('attributes', {}).get('country', {}).get('data', []):
            _item_name = _country_data_item.get('properties', {}).get('context')
            _item_value = _country_data_item.get('properties', {}).get('value')
            if not _item_name or not _item_value:
                continue
            country_data[_item_name] = country_data.get(_item_name) or set()
            country_data[_item_name].add(_item_value)
        domicile = ', '.join(list(country_data['domicile'])) if country_data.get('domicile') else ''

        # Url
        contact_data = {}
        for _contact_data_item in company.get('attributes', {}).get('contact', {}).get('data', []):
            _item_name = _contact_data_item.get('properties', {}).get('type')
            _item_value = _contact_data_item.get('properties', {}).get('value')
            if not _item_name or not _item_value:
                continue
            contact_data[_item_name] = contact_data.get(_item_name) or set()
            contact_data[_item_name].add(_item_value)
        contact_url = ', '.join(list(contact_data['url'])) if contact_data.get('url') else ''

        # Phone numbers
        phone_numbers = []
        websites = []
        for _contact in company.get('attributes', {}).get('contact', {}).get('data', []):
            _property = _contact.get('properties') or {}
            _property_type = ((_property.get('value') or _property.get('text')) or '').strip().lower() or None
            _property_value = ((_property.get('date') or _property.get('from_date')) or '').strip().lower() or None
            if _property_value and _property_type == 'phone_number':
                phone_numbers.append(_property_value)
            elif _property_value and _property_type == 'url':
                websites.append(_property_value)

        # Address
        possible_addresses = sorted(
            company.get('attributes', {}).get('address', {}).get('data', []),
            key=lambda x: x.get('record_count') or 0
        )
        best_address = None
        address_entities = []
        for possible_address in possible_addresses:
            company_address = possible_address.get('properties', {})
            # Ref. https://docs.sayari.com/attributes/#address
            address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(
                # Make sure address has a reproducible uuid that's unique (i.e. doesn't depend on null values
                # in case record is not present).
                company_address.get('record') or
                company_uuid
            )))
            street1 = ', '.join([
                company_address.get(_field) for _field in [
                    'house_number', 'house', 'po_box', 'building', 'entrance', 'staircase', 'level', 'unit',
                ] if company_address.get(_field)
            ]).strip()
            street2 = ', '.join([
                company_address.get(_field) for _field in [
                    'road', 'metro_station', 'suburb', 'city_district', 'city', 'state_district', 'island',
                ] if company_address.get(_field)
            ]).strip()
            region = ', '.join([
                company_address.get(_field) for _field in [
                    'state', 'country_region',
                ] if company_address.get(_field)
            ]).strip()
            postcode = (company_address.get('postcode') or '').strip()

            address_entity = {
                'id': address_uuid,
                'type': 'EntityAddress',
                'attributes': {
                    'Street1': street1,
                    'Street2': street2,
                    'Region': region,
                    'Postcode': postcode,
                }
            }
            address_entities.append(address_entity)
            if not best_address or list(best_address['attributes'].values()).count('') < list(address_entities[-1]['attributes'].values()).count(''):
                best_address = address_entity

        full_address = '-'
        if best_address:
            full_address = ', '.join([
                _fragment for _fragment in [
                    street1, street2, region, postcode,
                ] if _fragment
            ])

        # Construct Summary
        summary_lines = []
        summary_line = []
        if incorporation_date:
            summary_line.append(f'Incorporation Date: {incorporation_date}')
        if registration_date:
            summary_line.append(f'Registration Date: {registration_date}')
        if company_numbers:
            summary_line.append(f'Company no: {sorted(list(company_numbers))[0]}')
        if summary_line:  # add line 1
            summary_lines.append(' | '.join(summary_line))
            summary_line = []
        if full_address:
            summary_line.append(f'Address: {full_address}')
        if phone_numbers:
            summary_line.append(f'Phone no: {", ".join(phone_numbers)}')
        if websites:
            summary_line.append(f'Website: {", ".join(websites)}')
        if summary_line:  # add line 2
            summary_lines.append(' | '.join(summary_line))

        # Construct Subtitle
        subtitle_points = ['Company']
        if countries_list:
            subtitle_points.append(countries_list)
        if pep_sanction_risk_info:
            subtitle_points.append(pep_sanction_risk_info)

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': company['label'],
            'subTitle': ' | '.join(subtitle_points),
            'summary': '\n'.join(summary_lines),
            'source': 'Sayari API',
            'url': 'https://sayari.auth0.com/u/login',
            'entities': [
                {
                    'id': company_uuid,
                    'type': 'EntityBusiness',
                    'attributes': {
                        'Name': company['label'] or '',
                        'LocalName': company['label'] or '',
                        'Description': pep_sanction_risk_info,
                        'Status': company_status,
                        'Liquidated': company.get('closed') is True,
                        'IncorporationDate': incorporation_date or '',
                        'RegistrationCountry': domicile,
                        'VatNumber': vat_number,
                        'SicCode': sic_code,
                        'CompaniesHouseId': uk_company_number,
                        'Url': contact_url,
                    }
                }
            ]
        }

        # Relationship: Address
        for address_entity in address_entities:
            result['entities'].append(address_entity)
            result['entities'].append(create_relationship(company_uuid, address_entity['id'], 'Company Address'))

        # Relationship: Products and Businesses
        possible_businesses = []
        for relationship_type in ('owner_of', 'shareholder_of', 'has_subsidiary',):
            if 'data' in company.get('relationships', {}):
                possible_businesses += [
                    _business for _business in
                    company.get('relationships', {}).get('data', [])
                    if (
                        _business.get('target') and relationship_type in _business.get('types', {}) and
                        _business.get('target', {}).get('type') in ('intellectual_property', 'company',)
                    )
                ]
            else:
                possible_businesses += [
                    _business for _business in
                    company.get('relationships', {}).get(relationship_type, {}).get('data', [])
                    if (
                        _business.get('target') and relationship_type in _business.get('types', {}) and
                        _business.get('target', {}).get('type') in ('intellectual_property', 'company',)
                    )
                ]
        for business_relationship in possible_businesses:
            business = business_relationship['target']
            business_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, business['id']))
            business_shares_info = set()
            for _share_info in business_relationship.get('types', {}).get('shareholder_of', []):
                business_shares_info.add(', '.join(set([
                    _position.get('value')
                    for _position in _share_info.get('attributes', {}).get('position', [])
                    if _position.get('value')
                ])))
            result['entities'].append({
                'id': business_uuid,
                'type': 'EntityBusiness',
                'attributes': {
                    'Name': business['label'] or '',
                    'Status': 'Inactive' if business.get('closed') else 'Active',
                    'NumberOfShares': ', '.join(business_shares_info) if business_shares_info else '',
                }
            })
            result['entities'].append(create_relationship(company_uuid, business_uuid, 'Businesses'))

        # Relationship: Directors
        if 'data' in company.get('relationships', {}):
            possible_directors = [
                _business.get('target') for _business in
                company.get('relationships', {}).get('data', [])
                if (
                    _business.get('target', {}).get('type') == 'person' and
                    'director_of' in _business.get('target', {}).get('relationship_count', {}) and
                    'has_director' in _business.get('types', {})
                )
            ]
        else:
            possible_directors = [
                _business.get('target') for _business in
                company.get('relationships', {}).get('has_director', {}).get('data', [])
                if (
                    _business.get('target', {}).get('type') == 'person' and
                    'director_of' in _business.get('target', {}).get('relationship_count', {}) and
                    'has_director' in _business.get('types', {})
                )
            ]
        for person in possible_directors:
            person_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, person['id']))
            person_name_words = (person['label'] or '').split(' ')
            result['entities'].append({
                'id': person_uuid,
                'type': 'EntityDirectorRecord',
                'attributes': {
                    'FirstName': (person_name_words[0] if person_name_words else '').strip(),
                    'LastName': (' '.join(person_name_words[1:]) if person_name_words else '').strip(),
                    'JobTitle': 'Director'
                }
            })
            result['entities'].append(create_relationship(company_uuid, person_uuid, 'Directors'))

        # Relationship: Officers
        if 'data' in company.get('relationships', {}):
            possible_officers = [
                _business for _business in
                company.get('relationships', {}).get('data', [])
                if (
                    _business.get('target', {}).get('type') == 'person' and
                    'officer_of' in _business.get('target', {}).get('relationship_count', {}) and
                    'has_officer' in _business.get('types', {})
                )
            ]
        else:
            possible_officers = [
                _business for _business in
                company.get('relationships', {}).get('has_officer', {}).get('data', [])
                if (
                    _business.get('target', {}).get('type') == 'person' and
                    'officer_of' in _business.get('target', {}).get('relationship_count', {}) and
                    'has_officer' in _business.get('types', {})
                )
            ]
        for officer in possible_officers:
            person = officer['target']
            person_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, person['id']))
            person_name_words = (person['label'] or '').split(' ')
            job_title = ''
            for _record in officer['types'].get('has_officer', []):
                for _position in _record.get('attributes', {}).get('position', []):
                    if _position and _position.get('value'):
                        job_title = _position['value']
                        break
            result['entities'].append({
                'id': person_uuid,
                'type': 'EntityOfficerRecord',
                'attributes': {
                    'FirstName': (person_name_words[0] if person_name_words else '').strip(),
                    'LastName': (' '.join(person_name_words[1:]) if person_name_words else '').strip(),
                    'JobTitle': job_title,
                }
            })
            result['entities'].append(create_relationship(company_uuid, person_uuid, 'Officers'))

        search_results.append(result)

    return {'searchResults': search_results}


async def get_sayari_people(query: str, max_results: int = 50):
    search_results = []

    try:
        api = SayariAPIClient()
        api.fetch_token()
        api.make_client()
    except:
        return {'error': [{'message': 'Error establishing a connection with the Sayari API.'}]}

    try:
        response = api.client.get(api.url('search/entity'), params={
            'limit': max_results,
            'q': query,
            'filters': 'entity_type=person'
        })
        if not response.ok:
            return {'error': [{'message': 'Error response from Sayari API.'}]}
        people_list = response.json().get('data') or []
    except:
        return {'error': [{'message': 'Error querying the Sayari API.'}]}

    for listed_person in people_list:
        if listed_person['type'] != 'person':
            # In the people searcher, only return people, and not companies etc.
            continue

        try:
            response = api.client.get(api.url(listed_person['entity_url']))
            if not response.ok:
                print('Error fetching person. Returning partial result.', listed_person['url'], response.text)
                return search_results
            person = response.json()
        except:
            print('Error fetching person. Returning partial result.', listed_person['url'], response.text)
            return search_results

        person_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, person['id']))

        # Create search result
        countries_list = ', '.join(person.get('countries') or [])

        # Risk score
        pep_sanction_risk_info_points = []
        risk_value = person.get('risk', {}).get('cpi_score', {}).get('value') or ''
        if risk_value:
            pep_sanction_risk_info_points = [f'Risk Score: {risk_value}']
            if person['sanctioned']:
                pep_sanction_risk_info_points.append('Sanctioned')
            if person['pep']:
                pep_sanction_risk_info_points.append('PEP')
        pep_sanction_risk_info = ' - '.join(pep_sanction_risk_info_points)

        # Person number (ID number)
        person_numbers = set()
        for _identifier in person.get('identifiers') or []:
            _should_consider_identifier = (
                _identifier.get('value') and
                _identifier.get('label') and
                (_identifier.get('type') or '').lower() not in ('', 'unknown',)
            )
            if _should_consider_identifier:
                _person_number = f'{_identifier["value"]} ({_identifier["label"].replace("_", " ").upper()})'
                person_numbers.add(_person_number)

        # Address
        possible_addresses = sorted(
            person.get('attributes', {}).get('address', {}).get('data', []),
            key=lambda x: x.get('record_count') or 0
        )
        best_address = None
        address_entities = []
        for possible_address in possible_addresses:
            person_address = possible_address.get('properties', {})
            # Ref. https://docs.sayari.com/attributes/#address
            address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(
                # Make sure address has a reproducible uuid that's unique (i.e. doesn't depend on null values
                # in case record is not present).
                person_address.get('record') or
                person_uuid
            )))
            street1 = ', '.join([
                person_address.get(_field) for _field in [
                    'house_number', 'house', 'po_box', 'building', 'entrance', 'staircase', 'level', 'unit',
                ] if person_address.get(_field)
            ]).strip()
            street2 = ', '.join([
                person_address.get(_field) for _field in [
                    'road', 'metro_station', 'suburb', 'city_district', 'city', 'state_district', 'island',
                ] if person_address.get(_field)
            ]).strip()
            region = ', '.join([
                person_address.get(_field) for _field in [
                    'state', 'country_region',
                ] if person_address.get(_field)
            ]).strip()
            postcode = (person_address.get('postcode') or '').strip()

            address_entity = {
                'id': address_uuid,
                'type': 'EntityAddress',
                'attributes': {
                    'Street1': street1,
                    'Street2': street2,
                    'Region': region,
                    'Postcode': postcode,
                }
            }
            address_entities.append(address_entity)
            if not best_address or list(best_address['attributes'].values()).count('') < list(address_entities[-1]['attributes'].values()).count(''):
                best_address = address_entity

        full_address = '-'
        if best_address:
            full_address = ', '.join([
                _fragment for _fragment in [
                    street1, street2, region, postcode,
                ] if _fragment
            ])

        # Nationality and Residence
        country_data = {}
        for _country_data_item in person.get('attributes', {}).get('country', {}).get('data', []):
            _item_name = _country_data_item.get('properties', {}).get('context')
            _item_value = _country_data_item.get('properties', {}).get('value')
            if not _item_name or not _item_value:
                continue
            country_data[_item_name] = country_data.get(_item_name) or set()
            country_data[_item_name].add(_item_value)
        nationality = ', '.join(list(country_data['nationality'])) if country_data.get('nationality') else ''
        residence = ', '.join(list(country_data['residence'])) if country_data.get('residence') else ''

        # Construct Summary
        summary_lines = []
        if person_numbers:
            summary_lines.append(f'Person no: {sorted(list(person_numbers))[0]}')
        if full_address:
            summary_lines.append(f'Address: {full_address}')

        # Construct Subtitle
        subtitle_points = ['Person']
        if countries_list:
            subtitle_points.append(countries_list)
        if pep_sanction_risk_info:
            subtitle_points.append(pep_sanction_risk_info)

        # Construct First Name and Last Name
        person_name_words = (person['label'] or '').split(' ')

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': person['label'],
            'subTitle': ' | '.join(subtitle_points),
            'summary': '\n'.join(summary_lines),
            'source': 'Sayari API',
            'url': 'https://sayari.auth0.com/u/login',
            'entities': [
                {
                    'id': person_uuid,
                    'type': 'EntityOfficerRecord',
                    'attributes': {
                        'IsCompany': False,
                        'FirstName': (person_name_words[0] if person_name_words else '').strip(),
                        'LastName': (' '.join(person_name_words[1:]) if person_name_words else '').strip(),
                        'Description': pep_sanction_risk_info,
                        'Dob': person.get('date_of_birth') or '',
                        'Nationality': nationality,
                        'RegistrationCountry': residence,
                    }
                }
            ]
        }

        # Relationship: Address
        for address_entity in address_entities:
            result['entities'].append(address_entity)
            result['entities'].append(create_relationship(person_uuid, address_entity['id'], 'Person Address'))

        # Relationship: Businesses
        possible_businesses = []
        for relationship_type in ('director_of', 'officer_of', 'shareholder_of', 'linked_to', 'registered_agent_of',):
            if 'data' in person.get('relationships', {}):
                possible_businesses += [
                    _business for _business in
                    person.get('relationships', {}).get('data', [])
                    if (
                        _business.get('target') and relationship_type in _business.get('types', {}) and
                        _business.get('target', {}).get('type') in ('intellectual_property', 'company',)
                    )
                ]
            else:
                possible_businesses += [
                    _business for _business in
                    person.get('relationships', {}).get(relationship_type, {}).get('data', [])
                    if (
                        _business.get('target') and relationship_type in _business.get('types', {}) and
                        _business.get('target', {}).get('type') in ('intellectual_property', 'company',)
                    )
                ]
        for business_relationship in possible_businesses:
            business = business_relationship['target']
            business_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, business['id']))

            business_shares_info = set()
            for _share_info in business_relationship.get('types', {}).get('shareholder_of', []):
                business_shares_info.add(', '.join(set([
                    _position.get('value')
                    for _position in _share_info.get('attributes', {}).get('position', [])
                    if _position.get('value')
                ])))
            business_shares_info -= set([''])

            job_titles_info = set()
            for _job_title in business_relationship.get('types', {}).get(relationship_type, []):
                job_titles_info.add(', '.join(set([
                    _position.get('value')
                    for _position in _job_title.get('attributes', {}).get('position', [])
                    if _position.get('value')
                ])))
            job_titles_info -= set([''])

            # Filtering out empty positions reduces some noise in the results. Comment out the following lines
            # if you want everything to be included.
            if not job_titles_info:
                continue

            result['entities'].append({
                'id': business_uuid,
                'type': 'EntityBusiness',
                'attributes': {
                    'Name': business['label'] or '',
                    'Status': 'Inactive' if business.get('closed') else 'Active',
                    'NumberOfShares': ', '.join(business_shares_info) if business_shares_info else '',
                    'JobTitle': ', '.join(job_titles_info) if job_titles_info else '',
                }
            })
            result['entities'].append(create_relationship(person_uuid, business_uuid, 'Businesses'))

        search_results.append(result)

    return {'searchResults': search_results}
