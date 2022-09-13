import csv
import json

# Create a ror_metadata.csv file from the JSON dump, with fields:
# ROR ID, NAME, Wikipedia URL, Inception, ISNI, Wikidata ID,
# City, Country, Inst type, website
# (for ISNI and Wikidata ID pick preferred ID, or first if none pref)
# NAME = main label, should be English or at least Latin script

ror_data_file = 'ror-data.json'

def get_first_value_if_any(ror_data, type):
    value = None
    if type in ror_data:
        list = ror_data[type]
        if len(list) > 0:
            value = list[0]
    return value

def get_best_external_id(ror_data, type):
    external_id_data = ror_data['external_ids']
    id_value = None
    if type in external_id_data:
        id_value = external_id_data[type]['preferred']
        if id_value is None:
            id_value = external_id_data[type]['all'][0]
    return id_value

with open(ror_data_file, 'r') as df:
    ror_data = json.load(df)

with open('ror_metadata.csv', 'w') as csvfile:
    ror_writer = csv.writer(csvfile)
    ror_writer.writerow(['ROR ID', 'Name', 'Wikipedia URL', 'Inception', 'ISNI', 'Wikidata ID', 'City', 'Country', 'Inst type', 'website'])
    for ror_entry in ror_data:
        ror_id = ror_entry['id'].split('/')[-1]
        name = ror_entry['name']
        type = get_first_value_if_any(ror_entry, 'types')
        website = get_first_value_if_any(ror_entry, 'links')
        wikipedia_url = ror_entry['wikipedia_url']
        inception = ror_entry['established']
        country = ror_entry['country']['country_name']
        city = None
        address = get_first_value_if_any(ror_entry, 'addresses')
        if address is not None:
            city = address['city']
        isni = get_best_external_id(ror_entry, 'ISNI')
        wikidata_id = get_best_external_id(ror_entry, 'Wikidata')
        ror_writer.writerow([ror_id, name, wikipedia_url, inception, isni, wikidata_id, city, country, type, website])
