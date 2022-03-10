# Gravatar

## Configuration

To enable or disable searchers, update `config.yml` and set "enabled" as `True` or `False`. Set `redirect` to the 
address of the adaptor you want to route that searcher to.  

```yaml 
    searchers:
      database:
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

The adaptors are written in Python 3.10 and make use of the FastAPI framework which runs on a uvicorn server.

Install the required packages:

    pip install -r requirements.txt

Run API on the uvicorn server:

    uvicorn main:app --host <IPv4 address>

The IPv4 ip address needs to be accessible to Videris so make sure you configure any necessary port forwarding rules.
    
