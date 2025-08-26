import csv
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen

sparql_api_url = 'https://query.wikidata.org/sparql'
user_agent = 'fetch_wikidata_ror_entries.py (https://github.com/arthurpsmith/wikidata-tools/tree/master/APSbot/ROR; arthurpsmith@gmail.com)'

def get_sparql(query):
    query_params = urlencode({'query': query, 'format': 'json'})
    headers = {'User-Agent': user_agent}
    url = '{0}?{1}'.format(sparql_api_url, query_params)
    req = Request(url, headers=headers)
    with urlopen(req) as response:
        raw = response.read()
    response_data = json.loads(raw.decode('utf-8'))
    return response_data['results']['bindings']


with open('wikidata_ror.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Wikidata ID', 'ROR ID', 'Deprecated'])
    ror_items = get_sparql("SELECT ?item ?ror ?deprecated WHERE { ?item p:P6782 ?stmt . ?stmt ps:P6782 ?ror; wikibase:rank ?rank . BIND(?rank = wikibase:DeprecatedRank AS ?deprecated) }")
    for ror_item in ror_items:
        qid = ror_item['item']['value'].split('/')[-1]
        ror_id = ror_item['ror']['value']
        deprecated = ror_item['deprecated']['value']
        writer.writerow([qid, ror_id, deprecated])
