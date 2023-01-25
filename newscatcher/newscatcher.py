#to do: 
# externalise auth
# add extra to result format

import requests
import uuid

#need to set this for auth - look to externalise before deploy?
j = 'BnOTaBwfkm3DfOdYBvxZRLkRjUyHYSYkPlRk0z-YOXM' #rate limited until mid feb 2023
m = "f1cChJ938l0Q774LeQZbJHJUJxYc_kLZk1tpdIFi_UE"
api_key = m

def get_news(query: str, maxResults = 10):
    url = "https://api.newscatcherapi.com/v2/search"
    headers = {
    "x-api-key": api_key
    }
    querystring = {"q":query,"lang":"en","sort_by":"relevancy","page":"1","page_size":maxResults}
    response = requests.request("GET", url, headers=headers, params=querystring)
    blob = response.json()
    if blob['status'] == "ok":
        search_results = []
        for x in blob['articles']:
            result = {
                'key': str(uuid.uuid4()).upper(),
                'title': x['title'],
                'subTitle': f"Domain: {x['clean_url']}    Topic: {x['topic'].title()}   Author: {x['author']}   Date: {x['published_date'][0:10]}",
                'summary': x['summary'],
                'source': 'NewsCatcherAPI',
                'entities': [{
                    'id': str(uuid.uuid3(uuid.NAMESPACE_DNS, x['link'])),
                    'type': 'EntityWebPage',
                    'attributes': 
                        {
                        'Url': x['link'],
                        'Description': x['title']
                        },
                    }],
                'url': x['link']
            }
            search_results.append(result)
        return {'searchResults': search_results}
    else:
        return {"errors":[{
            "message": blob["message"]
            }]}