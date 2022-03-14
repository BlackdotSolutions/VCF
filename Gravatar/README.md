# Gravatar

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml 
    searchers:
      gravatar:        # <<< Note this must be identical to the id
        id: gravatar   
        name: Gravatar
        hint: Search by email address
        tooltip: Find Gravatar profile by email address
        enabled: True
```

## Adaptors

### Gravatar

Gravatar.com is a platform that allows users to reuse the same profile and avatar across a variety of different
platforms - Wordpress being a significant participating platform.

This adaptor allows Videris users to search for the gravatar profiles by supplying the target's email address. If a
matching profile is found, it is returned along with entities for each of the linked accounts and email addresses listed
on the profile (Flickr, Facebook, Goodreads, Tumblr, Twitter, Wordpress).


## Enabling the adaptor

The adaptor is written in Python 3.10 and make use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

    pip install -r requirements.txt

Run API on the uvicorn server:

    uvicorn main:app --host <IPv4 address>

The IPv4 ip address needs to be accessible to Videris so make sure you configure any necessary port forwarding rules.
    
