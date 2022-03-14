# VCF Router

## Configuration

To enable or disable searchers, update `config.yml` and set "enabled" as `True` or `False`. Set `redirect` to the 
address of the adaptor you want to route that searcher to.  

```yaml 
    searchers:
      database:   # <<< This needs to match the id on the next line.
        id: database
        name: My internal database
        hint: Search by name
        tooltip: Search my company database
        enabled: True # True or False
        redirect: http://example-one.com/searchers/adaptor-id/results
      bitcoin:
        id: bitcoin
        name: BitCoin Abuse
        hint: Check for abused BitCoin wallets
        tooltip: Search by BitCoin wallet address
        enabled: True # True or False
        redirect: http://123.456.7.89:1011/searchers/other-adaptor-id/results
```

## Running the router

The adaptor is written in Python 3.10 and make use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

    pip install -r requirements.txt

Run API on the uvicorn server:

    uvicorn main:app --host <IPv4 address>

The IPv4 ip address needs to be accessible to Videris so make sure you configure any necessary port forwarding rules.
    
