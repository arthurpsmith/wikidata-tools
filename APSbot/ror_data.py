import json
import csv
from wikidataintegrator import wdi_core

class RorData:
    def __init__(self, filename):
        self.ror_lookup_hash = {}
        with open(filename) as ror_file:
            self.ror_full_data = json.load(ror_file)
            for inst in self.ror_full_data:
                ror_id = inst['id'].split('/')[-1]
                self.ror_lookup_hash[ror_id] = inst
        self.fetch_wikidata_relations()

    def fetch_wikidata_relations(self):
        results = wdi_core.WDItemEngine.execute_sparql_query(query="SELECT ?item ?ror WHERE { ?item p:P6782/ps:P6782 ?ror . }")
        self.ror_wikidata_links = {}
        for i in results['results']['bindings']:
            qid = i['item']['value'].split('/')[-1]
            ror_id = i['ror']['value']
            self.ror_wikidata_links[ror_id] = qid

    def verify_not_in_wikidata(self, ror_id):
        results = wdi_core.WDItemEngine.execute_sparql_query(
                query="SELECT ?item ?ror WHERE {{ ?item wdt:P6782 '{0}' . }}".format(ror_id))
        return len(results['results']['bindings']) == 0

    def load_country_map(self, country_map_file):
        self.country_map = {}
        with open(country_map_file) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                country, country_qid = row
                self.country_map[country] = country_qid

    def load_type_map(self, type_map_file):
        self.org_types_map = {}
        with open(type_map_file) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                type, type_qid = row
                self.org_types_map[type] = type_qid

    def all_valid_ids(self):
        valid_id_list = []
        for inst in self.ror_full_data:
            if 'name' in inst:
                valid_id_list.append(inst['id'].split('/')[-1])
        return valid_id_list

    def valid_ids_not_in_wikidata(self):
        id_list = []
        for ror_id in self.all_valid_ids():
            if ror_id not in self.ror_wikidata_links:
                id_list.append(ror_id)
        return id_list

    def base_data_for_id(self, ror_id):
        org = self.ror_lookup_hash[ror_id]
        org_name = org['name']
        org_inception = org['established']
        website = None
        city = None
        country = None
        org_type_label = 'Other' # default
        if org['types']:
            for type_label in org['types']:
                org_type_label = type_label
        org_type_qid = self.org_types_map[org_type_label]
        if org['links']:
            for link_url in org['links']:
                website = link_url.strip() # remove any extraneous spaces
        if org['addresses']:
            for org_address in org['addresses']:
                city = org_address['city']
        country = org['country']['country_name']
        org_country_qid = self.country_map[country]
        org_desc_list = []
        if org_type_label != 'Other':
            org_desc_list.append(org_type_label.lower())
        if (org_type_label != 'Company') and (org_type_label != 'Facility'):
            org_desc_list.append('organization')
        org_desc_list.append('in')
        if city:
            org_desc_list.append(city + ',')
        org_desc_list.append(country)
        org_description = ' '.join(org_desc_list)
        return {
            'ror_id': ror_id,
            'label': org_name,
            'description': org_description,
            'inception': org_inception,
            'type_qid': org_type_qid,
            'website': website,
            'country_qid': org_country_qid
        }

    def aliases_for_id(self, ror_id):
        org = self.ror_lookup_hash[ror_id]
        org_aliases = []
        if org['aliases']:
            for alias in org['aliases']:
                org_aliases.append(alias)
        if org['acronyms']:
            for acronym in org['acronyms']:
                org_aliases.append(acronym)
        return org_aliases

    def labels_for_id(self, ror_id):
        org = self.ror_lookup_hash[ror_id]
        org_labels = []
        if org['labels']:
            for label_hash in org['labels']:
                language = label_hash['iso639']
                label = label_hash['label']
                org_labels.append({'label':label,'language':language})
        return org_labels
