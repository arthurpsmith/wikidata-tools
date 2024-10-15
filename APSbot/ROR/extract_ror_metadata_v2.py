import csv
import json

# Create a ror_metadata.csv file from the JSON dump, with fields:
# ROR ID, NAME, Wikipedia URL, Inception, ISNI, Wikidata ID,
# City, Country, Inst type, website
# (for ISNI and Wikidata ID pick preferred ID, or first if none pref)
# NAME = main label, should be English or at least Latin script

ror_data_file = 'ror-data-v2.json'

def get_value_by_type(ror_data, field, type):
    value = None
    if field in ror_data:
        entries = ror_data[field]
        for entry in entries:
            if entry['type'] == type:
                value = entry['value']
    return value

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
    for external_id_record in external_id_data:
        if external_id_record['type'] == type:
            id_value = external_id_record['preferred']
            if id_value is None:
                id_value = external_id_record['all'][0]
    return id_value

def get_ror_display_name(ror_data):
    name_value = None
    names = ror_data['names']
    for name in names:
        if 'ror_display' in name['types']:
            name_value = name['value']
    return name_value

with open(ror_data_file, 'r') as df:
    ror_data = json.load(df)

with open('ror_metadata_v2.csv', 'w') as csvfile:
    ror_writer = csv.writer(csvfile)
    ror_writer.writerow(['ROR ID', 'Name', 'Wikipedia URL', 'Inception', 'ISNI', 'Wikidata ID', 'City', 'Country Code', 'Country', 'Inst type', 'website', 'status'])
    for ror_entry in ror_data:
        ror_id = ror_entry['id'].split('/')[-1]
        name = get_ror_display_name(ror_entry)
        type = get_first_value_if_any(ror_entry, 'types')
        website = get_value_by_type(ror_entry, 'links', 'website')
        wikipedia_url = get_value_by_type(ror_entry, 'links', 'wikipedia')
        inception = ror_entry['established']
        status = ror_entry['status']
        default_location = get_first_value_if_any(ror_entry, 'locations')
        if default_location:
            city_record = default_location['geonames_details']
            country = city_record['country_name']
            country_code = city_record['country_code']
            city = city_record['name']
        isni = get_best_external_id(ror_entry, 'isni')
        wikidata_id = get_best_external_id(ror_entry, 'wikidata')
        ror_writer.writerow([ror_id, name, wikipedia_url, inception, isni, wikidata_id, city, country_code, country, type, website, status])
