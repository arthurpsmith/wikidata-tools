import sys
import csv
import json
from urllib.parse import urlencode
from urllib.request import urlopen

api_url = 'https://www.wikidata.org/w/api.php'

def get_entities(qid_list):
    joined_ids = '|'.join(qid_list)
    query_params = urlencode({'action': 'wbgetentities', 'ids': joined_ids, 'format': 'json'})
    url = '{0}?{1}'.format(api_url, query_params)
    with urlopen(url) as response:
        raw = response.read()
    response_data = json.loads(raw.decode('utf-8'))
    return response_data['entities']


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx+n, l)]


wikidata_ids = []
input_file = sys.argv[1]
with open(input_file) as wdfile:
    reader = csv.reader(wdfile)
    for row in reader:
        wikidata_ids.append(row[0])

with open('wikidata_redirects.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Wikidata ID', 'Redirected ID'])
    for qid_list in batch(wikidata_ids, 50):
        wd_data = get_entities(qid_list)
        for qid in wd_data.keys():
            qid_info = wd_data[qid]
            if 'redirects' in qid_info:
                new_qid = qid_info['redirects']['to']
                writer.writerow([qid,new_qid])
