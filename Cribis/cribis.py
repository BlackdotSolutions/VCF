"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import os
import uuid

from vcf import create_relationship

import zeep


# ============================ CRIBIS functions ============================
CRIBIS_USERNAME = os.getenv('CRIBIS_USERNAME')
CRIBIS_PASSWORD = os.getenv('CRIBIS_PASSWORD')
CRIBIS_API_CALL_TIMEOUT = 15.0  # NOTE: API seems to be very slow. Set a sufficiently high value here.
CRIBIS_API_WSDL_URL = 'https://dis.cribis.com/Search/2012-04-20/?singleWsdl'
ITALY_COUNTRY_CODE = 'IT'


async def get_cribis_company(query: str, max_results: int = 100):
    client = zeep.Client(CRIBIS_API_WSDL_URL)
    search_results = []
    try:
        app_transaction_id = str(uuid.uuid4())
        response = client.service.CompanySearch(
            Username=CRIBIS_USERNAME,
            Password=CRIBIS_PASSWORD,
            ApplicationTransactionID=app_transaction_id,
            CustomerReferenceText=str(uuid.uuid4()),
            SearchData={
                'FlagActiveOnly': True,
                'FlagHQOnly': False,
                'MaximumHits': max_results,
                'CompanyName': query,
            }
        )
    except:
        return {'error': [{'message': 'Error querying the CRIBIS API.'}]}

    try:
        if response.TransactionResponse.Details.ApplicationTransactionID != app_transaction_id:
            return {'error': [{'message': 'Received an illegal response from the CRIBIS API. %s' % response}]}
    except AttributeError:
        print(response)
        return {'error': [{'message': 'Received an incomplete response from the CRIBIS API. %s' % response}]}

    try:
        if response.TransactionResponse.Result.Code not in ('OK', 'CS006',):
            '''
            Codes:
                OK      - Query is successful, and there are results present.
                CS006   - Query is successful, but no results found.
            '''
            return {'error': [{'message': 'Received an error response from the CRIBIS API. %s' % response}]}
    except AttributeError:
        print(response)
        return {'error': [{'message': 'Received an incomplete result from the CRIBIS API. %s' % response}]}

    try:
        company_list = (response.CompanyList.CompanyItem or []) if response.CompanyList else []
    except AttributeError:
        print(response)
        return {'error': [{'message': 'Received an incomplete company list from the CRIBIS API. %s' % response}]}
    for company in company_list:
        company_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, company['CrifNumber']))
        try:
            last_balance_data_str = company['LastBalanceDate'].strftime('%d/%m/%Y')
        except:
            last_balance_data_str = '-'

        description = (company['ActivityDescription'] or '').replace('\r', '').replace('\n', '\r\n')
        if len(description) > 150:
            description = f'{description[:150].strip()}...'

        # Create search result
        subtitle = f'Company Branch - {company["CrifNumber"]}'
        if company['UnitTypeCode'] == 'S':
            subtitle = f'Company Headquarters - {company["CrifNumber"]}'

        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': company['CompanyName'],
            'subTitle': subtitle,
            'summary': (
                f'Crif Number: {company["CrifNumber"] or "-"} | '
                f'VAT Number: {company["VATCode"] or "-"} | '
                f'Province: {company["ProvinceCode"] or "-"} | '
                f'Status: {company["ActivityStatusCodeDescription"] or "-"} | '
                f'Last Balance Date: {last_balance_data_str or "-"} | '
                f'Description: {description or "-"} | '
                f'Website: {company["WebSite"] or "-"}'
            ),
            'source': 'CRIBIS API',
            'url': (
                f'https://www2.cribisx.com/#Purchase/CompanyByDUNS/{company["DunsNumber"]}'
                if company['DunsNumber'] else 'https://www2.cribisx.com'
            ),
            'entities': [
                {
                    'id': company_uuid,
                    'type': 'EntityBusiness',
                    'attributes': {
                        'Name': company['CompanyName'] or '',
                        'LocalName': company['CompanyName'] or '',
                        'CompanyNumber': company['CrifNumber'] or '',
                        'VatNumber': company['VATCode'] or '',
                        'Status': company["ActivityStatusCodeDescription"] or '',
                        'Duns': company['DunsNumber'] or '',
                        'RegistrationState': company['Region'] or '',
                        'RegistrationCountry': ITALY_COUNTRY_CODE or '',
                        'Liquidated': company['FlagOutOfBusiness'] is True,
                        'TradeDescription': description or '',
                        'StatusSince': last_balance_data_str or '',
                    },
                },
            ],
        }

        if company['WebSite']:
            webpage_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, company['WebSite']))
            result['entities'].append({
                'id': webpage_uuid,
                'type': 'EntityWebPage',
                'attributes': {
                    'Url': company['WebSite'],
                },
            })
            result['entities'].append(create_relationship(company_uuid, webpage_uuid, 'Company Website'))

        search_results.append(result)

        if len(search_results) >= max_results:
            break

    return {'searchResults': search_results}


async def get_cribis_people(query: str, max_results: int = 100):
    client = zeep.Client(CRIBIS_API_WSDL_URL)
    search_results = []
    person_name_words = (query or '').split(' ')
    person_name = person_name_words[0]
    person_surname = ' '.join(person_name_words[1:])
    try:
        app_transaction_id = str(uuid.uuid4())
        response = client.service.PersonSearch(
            Username=CRIBIS_USERNAME,
            Password=CRIBIS_PASSWORD,
            ApplicationTransactionID=app_transaction_id,
            CustomerReferenceText=str(uuid.uuid4()),
            SearchData={
                'Name': person_name,
                'Surname': person_surname,
                'MaximumHits': max_results,
            }
        )
    except:
        return {'error': [{'message': 'Error querying the CRIBIS API.'}]}

    try:
        if response.TransactionResponse.Details.ApplicationTransactionID != app_transaction_id:
            return {'error': [{'message': 'Received an illegal response from the CRIBIS API. %s' % response}]}
    except AttributeError:
        print(response)
        return {'error': [{'message': 'Received an incomplete response from the CRIBIS API. %s' % response}]}

    try:
        if response.TransactionResponse.Result.Code == 'PS002':
            return {'error': [{'message': 'Please provide both the name and surname of the person to query. Eg. Jon Doe'}]}
        if response.TransactionResponse.Result.Code not in ('OK', 'PS004',):
            '''
            Codes:
                OK      - Query is successful, and there are results present.
                PS004   - Query is successful, but no results found.
            '''
            return {'error': [{'message': 'Received an error response from the CRIBIS API. %s' % response}]}
    except AttributeError:
        print(response)
        return {'error': [{'message': 'Received an incomplete result from the CRIBIS API. %s' % response}]}

    try:
        people_list = (response.PersonList.PersonItem or []) if response.PersonList else []
    except AttributeError:
        print(response)
        return {'error': [{'message': 'Received an incomplete people list from the CRIBIS API. %s' % response}]}

    for person in people_list:
        # Use a random string in case TAXCode is not present. If we just used a blank string, then if there are multiple
        # records present without TAXCode, then `person_uuid` would be the same for all of them - which is something we
        # do not want - as the whole purpose of uuid is to provide a unique id, and this will generate duplicates.
        person_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, person['TAXCode'] or str(uuid.uuid4())))
        try:
            birth_date = person['BirthDate'].strftime('%d/%m/%Y')
        except:
            birth_date = '-'

        full_address = person['Address'] or ''
        if person['Village']:
            full_address = f'{full_address}, {person["Village"]}' if full_address else person['Village']
        if person['Town']:
            full_address = f'{full_address}, {person["Town"]}' if full_address else person['Town']
        if person['Province']:
            full_address = f'{full_address}, {person["Province"]}' if full_address else person['Province']
        if person['Zip']:
            full_address = f'{full_address}, {person["Zip"]}' if full_address else person['Zip']

        # Create search result
        result = {
            'key': str(uuid.uuid4()).upper(),
            'title': f'{person["Name"]} {person["Surname"]}'.strip(),
            'subTitle': (
                f'Person ({person["Gender"] or "-"}) '
                f'DOB: {birth_date}. '
                f'Birth Town: {person["BirthTown"] or "-"}.'
            ),
            'summary': (
                f'Address: {full_address or "-"}.\n'
                f'Is Soletrader: {person["IsSoletrader"]}. '
                f'Is Shareholder: {person["IsShareholder"]}. '
                f'TAX Code: {person["TAXCode"] or "-"}.'
            ),
            'source': 'CRIBIS API',
            'url': 'https://www2.cribisx.com/Search/Person',
            'entities': [
                {
                    'id': person_uuid,
                    'type': 'EntityOfficerRecord',
                    'attributes': {
                        'FirstName': person['Name'] or '',
                        'LastName': person['Surname'] or '',
                        'Dob': birth_date,
                        'Gender': person['Gender'] or '',
                        'Nationality': person['Country'] or '',
                    },
                },
            ],
        }

        if full_address:
            address_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, full_address or ''))
            result['entities'].append({
                'id': address_uuid,
                'type': 'EntityAddress',
                'attributes': {
                    'Street1': person['Address'] or '',
                    'Street2': person['Village'] or '',
                    'Street3': person['Town'] or '',
                    'Region': person['Province'] or '',
                    'Postcode': person['Zip'] or '',
                },
            })
            result['entities'].append(create_relationship(person_uuid, address_uuid, 'Person Address'))

        search_results.append(result)

        if len(search_results) >= max_results:
            break

    return {'searchResults': search_results}
