import sys
import traceback
from wikidataintegrator import wdi_core, wdi_login
import json
import datetime
import ror_data
from time import sleep

# Property values from live wikidata:
p_ror_id = 'P6782'
p_instance_of = 'P31'
p_country = 'P17'
p_official_website = 'P856'
p_inception = 'P571'


def create_ror_item(ror_data, ror_id, ror_release_qid, login_instance):
    reference_info = [wdi_core.WDItemID(ror_release_qid, 'P248', is_reference=True), wdi_core.WDExternalID(ror_id, p_ror_id, is_reference=True)]
    base_data = ror_data.base_data_for_id(ror_id)
    org_name = base_data['label']
    org_description = base_data['description']
    org_type_qid = base_data['type_qid']
    org_country_qid = base_data['country_qid']
    website = base_data['website']
    org_inception = base_data['inception']
    org_aliases = ror_data.aliases_for_id(ror_id)
    org_labels = ror_data.labels_for_id(ror_id)

    statements = []
    statements.append(wdi_core.WDItemID(org_type_qid, p_instance_of, references=[reference_info]))
    statements.append(wdi_core.WDExternalID(ror_id, p_ror_id, references=[reference_info]))
    if org_country_qid:
        statements.append(wdi_core.WDItemID(org_country_qid, p_country, references=[reference_info]))
    if website and (len(website) < 500):
        statements.append(wdi_core.WDUrl(website, p_official_website, references=[reference_info]))
    if org_inception and (int(org_inception) > 900):
        org_inception_date = datetime.date(int(org_inception), 1, 1)
        statements.append(wdi_core.WDTime(org_inception_date.strftime('+%Y-%m-%dT%H:%M:%SZ'), p_inception, precision=9,
                                          references=[reference_info])) # year-level precision in inception dates from ROR
    wd_item = wdi_core.WDItemEngine(data=statements)
    wd_item.set_label(label=org_name,lang='en')
    wd_item.set_description(description=org_description,lang='en')
    if org_aliases and len(org_aliases) > 0:
        wd_item.set_aliases(org_aliases, lang='en')
    for label_hash in org_labels:
        if label_hash['language'] == 'en':
            wd_item.set_aliases([label_hash['label']], 'en', append=True)
        else:
            wd_item.set_label(label=label_hash['label'], lang=label_hash['language'])
    new_item_id = wd_item.write(login_instance, edit_summary='Creating item from ROR record via APSbot_ror_create script')
    print("created {0}".format(new_item_id))

#####
ror_release_qid = None
with open('ror_release_qid') as ror_release_file:
    line = ror_release_file.readline()
    ror_release_qid = line.rstrip()

ror_data = ror_data.RorData('../ror-data.json')
ror_data.load_country_map('country_map.csv')
ror_data.load_type_map('type_map.csv')

passwd = None

with open('apsbot.pwd') as passwdfile:
    passwd = passwdfile.read().strip()

login_instance = wdi_login.WDLogin(user='APSbot@APSbot', pwd=passwd)

entered_count = 0
min_entry = 0
max_entry = 2000
for ror_id in ror_data.valid_ids_not_in_wikidata():
    sleep(1.0) # crude throttle...
    entered_count += 1
    print("{0} - {1}".format(entered_count, ror_id))
    if entered_count < min_entry:
        continue
    try:
        create_ror_item(ror_data, ror_id, ror_release_qid, login_instance)
    except wdi_core.WDApiError as wd_error:
        print("Error creating ROR item for {0}: {1} - {2}".format(ror_id, sys.exc_info()[0], wd_error.wd_error_msg))
        traceback.print_exc()
    except KeyError as key_error:
        print("Error creating ROR item for {0}: {1} - {2}".format(ror_id, sys.exc_info()[0], str(key_error)))
        traceback.print_exc()
    except:
        print("Error creating ROR item for {0}: {1}".format(ror_id, sys.exc_info()[0]))
        traceback.print_exc()
    if entered_count >= max_entry:
        break
