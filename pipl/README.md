# Pipl

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml
searchers:
  pipl_people:
    id: pipl_people
    name: Pipl Search API
    hint: Enter the name of a person to search for
    tooltip: Get the Pipl Search API information of a person
    enabled: True

```

## Adaptors

### Pipl

Pipl is a digital identity and trust data provider. Pipl Search helps gather information on customers and contacts to ensure that companies are targeting the right people with the right content. This is useful in multiple industries like professional recruiting, finance, digital marketing and advertising.

This adaptor allows Videris users to search for the Pipl information of a person. If the person is found in Pipl, information like First Name, Last Name, Emails, Social Profiles are returned.


## Enabling the adaptor

The adaptor is written in Python 3.10 and makes use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

```
pip install -r requirements.txt
```

Configure mandatory environment variables:

```
export PIPL_API_KEY='xxxxx'
```

Run API on the uvicorn server:

```
uvicorn main:app --host <IPv4 address>
```

The IPv4 ip address needs to be accessible to Videris, so make sure you configure any necessary port forwarding rules.
