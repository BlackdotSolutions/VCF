# Little Sis

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml 
    searchers:
      littlesis:        # <<< Note this must be identical to the id
        id: littlesis   
        name: Little Sis
        hint: Search by name
        tooltip: Search for people or organisations
        enabled: True
```

## Little Sis

[LittleSis.org](https://LittleSis.org) is a free database of who-knows-who at the heights of business and government. It seems to be quite
US-centric but holds a large network, connecting the dots between the world's most powerful people and organizations.

This adaptor allows Videris users to search for people or organisations by name. The adaptor (mostly) respects the
maxResults parameter sent from Videris.

Results will be returned for each matching entity, which will be either a person or an organisation. Clicking the link
in the search results will take you to the entity's profile on LittleSis.org.

If the result has an associated website, this will be returned as a webpage entity, linked to the result (if copied
to/viewed in a Chart/Grid).

The top (first) 10 results will also have a subset (up to 15) of the entity's connections, which can also be shown in a
Chart/Grid. The results are sorted by the connected entity's link_count. Again, if those connections have websites, they
will be returned too.

The searcher also does a limited search for relationship details (gets the first 150 relationships). Where available,
the details will be added to the relationships for the (15 or fewer) connections mentioned above. Otherwise, blank
relationships are created from the main entity to their connections. Note: If the entity has more than 150 connections,
then it becomes increasingly unlikely that the relationship details retrieved happen to be for the 15 connections
returned (the same sorting is not applied).

## Enabling the adaptor

The adaptor is written in Python 3.10 and make use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

    pip install -r requirements.txt

Run API on the uvicorn server:

    uvicorn main:app --host <IPv4 address>

The IPv4 ip address needs to be accessible to Videris so make sure you configure any necessary port forwarding rules.
    
