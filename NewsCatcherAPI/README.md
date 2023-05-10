# NewsCatcher

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml 
    searchers:
      newscatcher:        # <<< Note this must be identical to the id
        id: newscatcher   
        name: NewsCatcher
        hint: null
        tooltip: Search for News with the NewsCatcher API
        enabled: True
```

## Adaptors

### NewsCatcher

NewsCatcher allows you to search multi-language worldwide news articles published online.

See https://newscatcherapi.com/ for more details and apply for an api_key, which needs to be included in auth.py.

## Enabling the adaptor

The adaptor is written in Python 3.10 and make use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

    pip install -r requirements.txt

Run API on the uvicorn server:

    uvicorn main:app --host <IPv4 address>

The IPv4 ip address needs to be accessible to Videris so make sure you configure any necessary port forwarding rules.