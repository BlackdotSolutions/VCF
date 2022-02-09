"""
To start the API, in a terminal window run:

    uvicorn main:app --host <ip address>

E.g.

    uvicorn main:app --host 192.168.2.25
"""

import yaml
from fastapi import FastAPI, status

from vcf import *
from gravatar import *
from littlesis import *

app = FastAPI()

with open('config.yml', 'r') as file:
    CONFIG = yaml.safe_load(file)


@app.get("/searchers/", response_model=List[Searcher], response_model_exclude_none=True)
def get_searchers():
    searchers = []

    for searcher in CONFIG["searchers"].values():
        if searcher["enabled"]:
            searcher.pop("enabled", None)
            searcher.pop("redirect", None)
            searchers.append(searcher)

    return searchers


@app.get("/searchers/{searcher_id}/results", response_model=SearchResults, response_model_exclude_none=True,
         status_code=status.HTTP_200_OK)
async def get_results(searcher_id, query: str, maxResults=50):
    if searcher_id in CONFIG["searchers"]:
        if CONFIG["searchers"][searcher_id]["enabled"]:
            if CONFIG["searchers"][searcher_id]["redirect"]:
                endpoint = CONFIG["searchers"][searcher_id]["redirect"] + f"?query={query}&maxResults={maxResults}"
                return requests.get(endpoint)
            else:
                return await globals()["get_" + searcher_id](query, maxResults)

        else:
            return {"errors": [{"message": "Searcher not enabled."}]}
    else:
        return {"errors": [{"message": "Unrecognised searcher"}]}
