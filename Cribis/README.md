# CRIBIS

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml
searchers:
  cribis_company:        # <<< Note this must be identical to the id
    id: cribis_company
    name: CRIBIS Company Search API
    hint: Enter a company to search for
    tooltip: Get the CRIBIS information of a company
    enabled: True
  cribis_people:
    id: cribis_people
    name: CRIBIS People Search API
    hint: Enter a person to search for
    tooltip: Get the CRIBIS information of a person
    enabled: True
```

## Adaptors

### CRIBIS

CRIBIS is the leading company in Italy in services for the management of trade credit and business development in Italy and abroad. CRIBIS is a company of CRIF , a group specialising in credit information systems (SIC), business information and credit management solutions, which offers qualified support to banks, financial companies, trust companies, insurance companies, telecommunications companies, utilities and businesses.

This adaptor allows Videris users to search for the CRIBIS information of a company or person. If the company or person is found in CRIBIS, information like DOB, REA Number, CRIF Number, Tax Code and DUNS Number are returned.


## Enabling the adaptor

The adaptor is written in Python 3.10 and makes use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

```
pip install -r requirements.txt
```

Configure environment variables:

```
export CRIBIS_USERNAME='XX000000'
export CRIBIS_PASSWORD='StrongPassword!100'
```

Run API on the uvicorn server:

```
uvicorn main:app --host <IPv4 address>
```

The IPv4 ip address needs to be accessible to Videris, so make sure you configure any necessary port forwarding rules.
