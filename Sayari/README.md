# Sayari

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml
searchers:
  sayari_company:        # <<< Note this must be identical to the id
    id: sayari_company
    name: Sayari Company Search Graph API
    hint: Enter a company to search for
    tooltip: Get the Sayari Graph information of a company
    enabled: True
  sayari_people:
    id: sayari_people
    name: Sayari People Search Graph API
    hint: Enter a person to search for
    tooltip: Get the Sayari Graph information of a person
    enabled: True
```

## Adaptors

### Sayari

Sayari is the Commercial Risk Intelligence Platform built to provide worldwide visibility into the relationships between businesses and individuals.

This adaptor allows Videris users to search for the Sayari information of a company or person. If the company is found in Sayari, information like Name, Status, Address, Risk Score, Incorporation Date are returned. If the person is found in Sayari, information like First Name, Last Name, Nationality, Date of Birth, Risk Score are returned.


## Enabling the adaptor

The adaptor is written in Python 3.10 and makes use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

```
pip install -r requirements.txt
```

Configure environment variables:

```
export SAYARI_CLIENT_ID='XX000000'
export SAYARI_CLIENT_SECRET='YY000000'
```

Run API on the uvicorn server:

```
uvicorn main:app --host <IPv4 address>
```

The IPv4 ip address needs to be accessible to Videris, so make sure you configure any necessary port forwarding rules.
