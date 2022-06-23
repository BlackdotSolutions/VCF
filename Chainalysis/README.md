# Chainalysis

## API Key & Usage

You must source an API key directly for the Chainalysis Sanctions API from Chainalysis, and you must comply with their license and usage restrictions.

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml
searchers:
  chainalysis:        # <<< Note this must be identical to the id
    id: chainalysis
    name: Chainalysis
    hint: Search by wallet address
    tooltip: Check if cyptocurrency wallet is sanctioned
    enabled: True
```

## Adaptors

### Chainalysis

Chainalysis is a blockchain data platform providing data, market intelligence and research to government agencies, exchanges, financial institutions, and insurance and cybersecurity companies.

This adaptor allows Videris users to search whether a cryptocurrency wallet address has been included in a sanctions designation. If sanctions are found, the OFAC name, description and URL of each sanction is returned. The OFAC URL contains more information about the sanctioned wallet.


## Enabling the adaptor

The adaptor is written in Python 3.10 and makes use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

```
pip install -r requirements.txt
```

Configure environment variables:

```
export CHAINALYSIS_API_KEY=YOUR_API_KEY
```

Run API on the uvicorn server:

```
uvicorn main:app --host <IPv4 address>
```

The IPv4 ip address needs to be accessible to Videris, so make sure you configure any necessary port forwarding rules.

## Example in Videris
![2022-06-13_10-12-16](https://user-images.githubusercontent.com/87775802/175311324-8bc80b50-7763-4071-839b-f044b1151e44.jpg)

