import os
import re
import traceback
import uuid
from datetime import datetime

from piplapis.search import SearchAPIRequest, SearchAPIError

from vcf import create_relationship


PIPL_API_KEY = os.getenv('PIPL_API_KEY')
MATCH_THRESHOLD = 0.01
EMAIL_REGEX = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]+$')
PHONE_REGEX = re.compile(r'^(\+\d{1,2})?\(?\d{3}\)?[.-]?\d{3}[.-]?\d{4}$')
# Ref. https://docs.pipl.com/reference/using-search-parameters
PIPL_VALID_SEARCH_QUERY_PARAMS = [
    'email', 'phone', 'username', 'user_id', 'url', 'first_name', 'last_name', 'middle_name',
    'raw_name', 'country', 'state', 'city', 'street', 'house', 'zipcode', 'raw_address',
    'age',
]
# We check for these inside the person object to make sure the results contain whatever
# fields we queried by. For example, if we query by email, then email should be present
# in the result; if we query by an address component like city, then an address must be
# present in the results etc.
PIPL_EQUIVALENT_RESULT_KEYS = {
    'email': 'emails',
    'phone': 'phones',
    'username': 'usernames',
    'user_id': 'user_ids',
    'url': 'urls',
    'first_name': 'names',
    'last_name': 'names',
    'middle_name': 'names',
    'raw_name': 'names',
    'country': 'origin_countries',
    'state': 'addresses',
    'city': 'addresses',
    'street': 'addresses',
    'house': 'addresses',
    'zipcode': 'addresses',
    'raw_address': 'addresses',
    'age': 'dob',
}
PIPL_SOCIAL_PROFILES = {
    'facebook': 'EntityFacebookProfile',
    'linkedin': 'EntityLinkedinProfile',
    'twitter': 'EntityTwitterProfile',
    'ebay': 'EntityEbayProfile',
    'google': 'EntityGooglePlusProfile',
    'pinterest': 'EntityPinterestProfile',
    'instagram': 'EntityInstagramProfile',
    'flickr': 'EntityFlickrProfile',
    'youtube': 'EntityYoutubeProfile',
    'odnoklassniki': 'EntityOdnoklassnikiProfile',
    'vk': 'EntityVkontakteProfile',
    'soundcloud': 'EntitySoundcloudProfile',
    'tiktok': 'EntityTiktokProfile',
}


SearchAPIRequest.set_default_settings(api_key=PIPL_API_KEY)


def log(*message):
    print(datetime.now().isoformat(), *message)


def normalize_label(label):
    if label == 'name':
        return 'raw_name'
    elif label == 'address':
        return 'raw_address'
    return label


# ============================ Pipl functions ============================
async def get_pipl_people(query: str, max_results: int = 50):
    search_results = []

    '''
    Scenarios for inputs:

    1.  Raw query that is a valid email or phone number. Eg. foo@example.com. In this case, we
        will search using the email field. Eg. +61401479979. In this case, we will search using
        the phone field. Please note that the `+` in phone number country codes has to be encoded
        as `%2B` in order for it to be passed to the backend as a literal `+` value; if not, most
        HTTP clients will consider `+` as the equivalent of a space character and strip it from
        the input.
    2.  Raw query that is not a valid email. eg. Jon Doe. In this case, we will
        search using the raw_name field.
    3.  Labeled list of query values.
        Eg. name:Jon Doe, email:"foo@example.com", address:"123, baker st".
        The multiple labeled values are delimited using a semi-colon (";"). In
        this case, we will search using the multiple fields provided.

    NOTE:
    *   If an invalid labeled field is provided, we will ignore it, and perform the
        search if that field were not provided.
    *   If free form values are mixed with labeled values in the input, then the free
        form values will be ignored, and just the labeled values will be considered.
    '''
    query = query.strip()
    query_components = [
        _component.strip() for _component in query.split(';')
        if _component.strip()
    ]
    search_params = {}
    if (len(query_components) == 1 and ':' in query_components[0]) or len(query_components) > 1:
        for query_component in query_components:
            try:
                query_label_index = query_component.index(':')
                query_label = normalize_label(query_component[:query_label_index].strip().strip('"\''))
                if query_label not in PIPL_VALID_SEARCH_QUERY_PARAMS:
                    raise Warning(f'Invalid label provided: {query_label}')
                query_value = query_component[query_label_index + 1:].strip().strip('"\'')
                search_params[query_label] = query_value
            except ValueError as e:
                log('Error in input query component:', query_component, 'error:', e)
                traceback.print_exc()
                continue
            except Warning as e:
                # Safely ignore warnings.
                log('Got a warning when processing input query component:', query_component, 'warning:', e)
                traceback.print_exc()
                continue
    else:
        if EMAIL_REGEX.findall(query):
            search_params['email'] = query
        elif PHONE_REGEX.findall(query.replace(' ', '')):
            search_params['phone'] = query
        else:
            search_params['raw_name'] = query

    if not search_params:
        log('No valid search params found, with raw query:', query)
        return {'error': [{'message': 'Error in the input query. Please provide a valid input.'}]}

    try:
        request = SearchAPIRequest(**search_params)
        response = request.send()
    except ValueError as e:
        log('Error in input query', e)
        traceback.print_exc()
        return {'error': [{'message': 'Error in the input query. Please provide a valid input.'}]}
    except SearchAPIError as e:
        log(e.http_status_code, e)
        traceback.print_exc()
        return {'error': [{'message': 'Error response from Pipl Search API.', 'http_status_code': e.http_status_code}]}

    entities = [response.person] if response.person else response.possible_persons
    for entity in entities:
        # Check match threshold
        if entity.match <= MATCH_THRESHOLD:
            log('Found entity with match score below threshold. Entity:', entity.person_id or entity.search_pointer)
            continue

        # Check if fields we queried by are present in the response
        try:
            for search_param in search_params:
                if PIPL_EQUIVALENT_RESULT_KEYS.get(search_param) and not getattr(entity, PIPL_EQUIVALENT_RESULT_KEYS[search_param], None):
                    raise Exception(
                        f'Queried with field "{search_param}", but equivalent field "{PIPL_EQUIVALENT_RESULT_KEYS[search_param]}" not '
                        f'found in the response or is empty.'
                    )
        except Exception as e:
            log('Excluding entity from result:', entity.person_id or entity.search_pointer, 'Reason:', e)
            continue

        if entity.person_id:
            entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, entity.person_id))
        elif entity.search_pointer:
            try:
                request = SearchAPIRequest(search_pointer=entity.search_pointer)
                response = request.send()
                if response.person and response.person.person_id:
                    entity = response.person
                    entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, entity.person_id))
                else:
                    log('Error getting person with search_pointer', entity.search_pointer, 'Response:', response.to_dict())
                    continue
            except SearchAPIError as e:
                log(e.http_status_code, e, 'Error searching with search_pointer', entity.search_pointer)
                traceback.print_exc()
                continue
        else:
            log('Found neither person_id nor search_pointer for entity. Entity:', entity.to_dict())
            continue


        # Address
        possible_addresses = entity.addresses or []
        address_entities = []
        for entity_address in possible_addresses:
            street1 = (entity_address.house or '').strip()
            if entity_address.apartment:
                street1 = (f'{street1}-{entity_address.apartment}' or '').strip()
            street2 = (entity_address.street or '').strip()
            city = (entity_address.city or '').strip()
            region = (entity_address.state_full or '').strip()
            postcode = (entity_address.zip_code or '').strip()
            country = (entity_address.country_full or '').strip()

            full_address = ', '.join([
                _fragment for _fragment in [
                    street1, street2, city, region, postcode, country,
                ] if _fragment
            ]) or '-'

            address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(
                # Make sure address has a reproducible uuid that's unique (i.e. doesn't depend on null values
                # in case record is not present).
                full_address or
                entity_uuid
            )))
            address_entity = {
                'id': address_uuid,
                'type': 'EntityAddress',
                'attributes': {
                    'Street1': street1,
                    'Street2': street2,
                    'City': city,
                    'Region': region,
                    'Postcode': postcode,
                    'Country': country,
                }
            }
            address_entities.append(address_entity)

        # Phone number
        possible_phones = entity.phones or []
        phone_entities = []
        for entity_phone in possible_phones:
            phone_number = (entity_phone.display or '').strip()
            phone_number_international = (entity_phone.display_international or '').strip()
            if not phone_number and not phone_number_international:
                continue

            phone_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(phone_number or phone_number_international )))
            phone_entity = {
                'id': phone_uuid,
                'type': 'EntityPhoneNumber',
                'attributes': {
                    'LocalNumber': phone_number,
                    'FormattedNumber': phone_number_international,
                }
            }
            phone_entities.append(phone_entity)

        # Email
        possible_emails = entity.emails or []
        email_entities = []
        for entity_email in possible_emails:
            email_address = (entity_email.address or '').strip()
            if not email_address:
                continue

            email_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(email_address)))
            email_entity = {
                'id': email_uuid,
                'type': 'EntityEmail',
                'attributes': {
                    'EmailAddress': email_address,
                }
            }
            email_entities.append(email_entity)

        # Name
        first_name = last_name = ''
        possible_names = entity.names or []
        best_possible_names = sorted(possible_names, key=lambda x: x.valid_since or datetime.min, reverse=True)  # most recent name is used
        if best_possible_names:
            best_possible_name = best_possible_names[0]
            first_name = (best_possible_name.first or '').strip() or '-'
            last_name = (best_possible_name.last or '').strip() or '-'

        # Nationality
        nationality = ''
        possible_countries = entity.origin_countries or []
        best_possible_countries = sorted(possible_countries, key=lambda x: x.valid_since or x.last_seen or datetime.min)  # oldest country is used
        if best_possible_countries:
            best_possible_country = best_possible_countries[0]
            nationality = (best_possible_country.display or '').strip() or '-'

        # Education
        education = ', '.join([
            _education.display for _education in sorted(
                entity.educations,
                key=lambda x: x.date_range.start if x.date_range else datetime.min.date(), reverse=True,
            )
        ])

        # Job
        job = ''
        best_possible_job = None
        possible_jobs = entity.jobs or []
        best_possible_jobs = sorted(possible_jobs, key=lambda x: x.date_range.start if x.date_range else datetime.min.date(), reverse=True)  # we want the latest job
        if best_possible_jobs:
            best_possible_job = best_possible_jobs[0]
            job =(best_possible_job.display or '').strip() or '-'

        # Url
        url = ''
        social_entities = []
        possible_urls = entity.urls or []
        best_possible_urls = sorted(possible_urls, key=lambda x: x.valid_since or x.last_seen or datetime.min)  # oldest country is used
        for _url in best_possible_urls:
            possible_url = (_url.url or '').strip()
            if not possible_url:
                continue

            # Use the first non-null match as the URL of the entity, but all non-null URLs can
            # figure in social entities.
            url = url or possible_url

            url_type = (_url.name or '').lower()
            social_type = PIPL_SOCIAL_PROFILES.get(url_type) or 'EntityGenericOnlineProfile'
            social_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(possible_url)))

            print('\n\nurl_type', url_type, 'social_type', social_type, 'entity', _url.to_dict())

            social_entity = {
                'id': social_uuid,
                'type': social_type,
                'attributes': {
                    'Url': possible_url,
                }
            }
            social_entities.append(social_entity)

        # Create search result
        title = ' | '.join([name.display for name in entity.names]).strip() or '(no name)'
        subtitle_chunks = []
        if entity.gender:
            subtitle_chunks.append(f'Gender: {entity.gender.display}')
        if job:
            subtitle_chunks.append(f'Job: {job}')
        if url:
            subtitle_chunks.append(f'URL: {url}')
        subtitle = ' | '.join(subtitle_chunks)

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': title,
            'subTitle': subtitle,
            'summary': '',
            'source': 'Pipl Search API',
            'url': url,
            'entities': [
                {
                    'id': entity_uuid,
                    'type': 'EntityPerson',
                    'attributes': {
                        'FirstName': first_name,
                        'LastName': last_name,
                        'Dob': ((entity.dob.display or '').strip() or '-') if entity.dob else '-',
                        'Education': education,
                        'Nationality': nationality,
                    }
                }
            ]
        }

        # Relationship: Address
        for address_entity in address_entities:
            result['entities'].append(address_entity)
            result['entities'].append(create_relationship(entity_uuid, address_entity['id'], 'Person Address'))

        # Relationship: Phone Numbers
        for phone_entity in phone_entities:
            result['entities'].append(phone_entity)
            result['entities'].append(create_relationship(entity_uuid, phone_entity['id'], 'Person Phone Number'))

        # Relationship: Email Addresses
        for email_entity in email_entities:
            result['entities'].append(email_entity)
            result['entities'].append(create_relationship(entity_uuid, email_entity['id'], 'Person Email Address'))

        # Relationship: Social Profiles / URLs
        for social_entity in social_entities:
            result['entities'].append(social_entity)
            result['entities'].append(create_relationship(entity_uuid, social_entity['id'], 'Person Online Profile'))

        # Relationship: Company / Job
        if best_possible_job:
            relation_entity = {
                'id': str(uuid.uuid4()).upper(),
                'type': 'EntityBusiness',
                'attributes': {
                    'Name': (best_possible_job.organization or '').strip(),
                    'LocalName': (best_possible_job.organization or '').strip(),
                    'JobTitle': (best_possible_job.title or '').strip(),
                }
            }
            result['entities'].append(relation_entity)
            result['entities'].append(create_relationship(entity_uuid, relation_entity['id'], 'Company'))

        search_results.append(result)

        if len(search_results) >= max_results:
            break

    return {'searchResults': search_results}
