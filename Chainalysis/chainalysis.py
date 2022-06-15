"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""
import os
import uuid

from vcf import create_relationship

import requests


# ============================ Chainalysis functions ============================
CHAINALYSIS_API_KEY = os.getenv('CHAINALYSIS_API_KEY')
CHAINALYSIS_API_CALL_TIMEOUT = 3.0
CHAINALYSIS_API_SANCTIONS_ENDPOINT = 'https://public.chainalysis.com/api/v1/address/{wallet_address}'


async def get_chainalysis(query: str, max_results=100):
    api = requests.Session()
    api.headers.update({
        'X-API-KEY': CHAINALYSIS_API_KEY,
    })

    '''
    Query can be in of the following formats, or a mix of these:
        - a single wallet address
        - a list of space-separated wallet addresses
        - a list of wallet addresses of the form (addr1xyz OR addr2xyz)
        - a wallet address enclosed in quotes (" or ')
        - any of these with duplicates present (i.e. same wallet address mentioned more than once)
        - a wallet address may or may not contain a leading '0x'. Duplicates must be considered
          taking this also into account.
    '''
    wallet_addresses = []
    for _wallet_address in query.replace('%20', ' ').split(' '):
        _wallet_address = _wallet_address.strip(' ()"\'')
        _should_add_wallet_address = (
            _wallet_address and
            (_wallet_address.lower() not in ['or',]) and
            (_wallet_address not in wallet_addresses) and
            (
                _wallet_address[2:] not in wallet_addresses
                if _wallet_address.startswith('0x')
                else True
            ) and
            (
                f'0x{_wallet_address}' not in wallet_addresses
                if not _wallet_address.startswith('0x')
                else True
            )
        )
        if _should_add_wallet_address:
            wallet_addresses.append(_wallet_address)

    # The Chainalysis Sanctions API allows only one address to be queried at a time, so query each wallet
    # address one by one, and append to the search results.
    search_results = []
    for queried_wallet_count, wallet_address in enumerate(wallet_addresses):
        try:
            response = api.get(
                CHAINALYSIS_API_SANCTIONS_ENDPOINT.format(**{'wallet_address': wallet_address}),
                timeout=CHAINALYSIS_API_CALL_TIMEOUT,
            )
            data: dict = response.json()
        except requests.RequestException:
            return {'error': [{'message': 'Error querying the Chainalysis API.'}]}

        if response.status_code != 200 or 'identifications' not in data:
            if queried_wallet_count > 0 and search_results:
                # In case multiple wallets are queried, and we error out after querying atleast one wallet,
                # the return the search results we have so far instead of erroring out completely.
                return {'searchResults': search_results}
            return {'error': [{'message': data.get('message') or data}]}

        # The Chainalysis Sanctions API has no way of specifying page length or page number, so everything
        # is returned all at once. We will limit the number of returned items to `max_results`.
        for sanction_index, sanction in enumerate(data['identifications']):
            sanction_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, sanction['name']))
            webpage_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, sanction['url']))

            # wallet_address may or may not containt the leading `0x` hex identifier. We should be
            # able to strip the wallet address from the name irrespective whether `0x` is present or not.
            org_name = sanction['name']
            if '0x' + wallet_address in org_name:
                org_name = org_name.replace('0x' + wallet_address, '')
            elif wallet_address in org_name:
                org_name = org_name.replace(wallet_address, '')
            elif wallet_address.startswith('0x') and wallet_address[2:] in org_name:
                org_name = org_name.replace(wallet_address[2:], '')
            org_name = org_name.strip()
            org_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, org_name))

            # Create search result
            result = {
                'key': str(uuid.uuid4()).upper(),
                'title': wallet_address,
                'subTitle': sanction['name'],
                'summary': sanction['description'],
                'source': 'Chainalysis Sanctions API',
                'entities': [
                    {
                        'id': sanction_uuid,
                        'type': 'EntityAsset',
                        'attributes': {
                            'Name': wallet_address,
                            'Url': sanction['url'],
                        },
                    },
                    {
                        'id': webpage_uuid,
                        'type': 'EntityWebPage',
                        'attributes': {
                            'Url': sanction['url'],
                        },
                    },
                    create_relationship(sanction_uuid, webpage_uuid, 'Sanctioned URL'),
                    {
                        'id': org_uuid,
                        'type': 'EntityOrganisation',
                        'attributes': {
                            'Name': org_name,
                        },
                    },
                    create_relationship(sanction_uuid, org_uuid, 'Sanction Name'),
                ],
                'url': sanction['url'],
            }
            search_results.append(result)

    return {'searchResults': search_results}
