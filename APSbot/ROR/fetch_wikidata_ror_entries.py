import csv
import json
from urllib.parse import urlencode
from urllib.request import urlopen

sparql_api_url = 'https://query.wikidata.org/sparql'

def get_sparql(query):
    query_params = urlencode({'query': query, 'format': 'json'})
    url = '{0}?{1}'.format(sparql_api_url, query_params)
    with urlopen(url) as response:
        raw = response.read()
    response_data = json.loads(raw.decode('utf-8'))
    return response_data['results']['bindings']


with open('wikidata_ror.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Wikidata ID', 'ROR ID'])
    ror_items = get_sparql("SELECT ?item ?ror WHERE { ?item p:P6782 ?stmt . ?stmt ps:P6782 ?ror; wikibase:rank ?rank .  FILTER(?rank != wikibase:DeprecatedRank) }")
    for ror_item in ror_items:
        qid = ror_item['item']['value'].split('/')[-1]
        ror_id = ror_item['ror']['value']
        writer.writerow([qid, ror_id])
