import sys
from wikidataintegrator import wdi_core, wdi_login
import json
import datetime
import wdi_extension
import grid_data

# Property values from live wikidata:
p_grid_id = 'P2427'
p_instance_of = 'P31'
p_country = 'P17'
p_official_website = 'P856'
p_inception = 'P571'
p_coordinate_location = 'P625'

passwd = None

with open('apsbot.pwd') as passwdfile:
    passwd = passwdfile.read().strip()

login_instance = wdi_login.WDLogin(user='APSbot', pwd=passwd)

release_date = None
release_url = None
release_doi = None
grid_wdid = None
with open('grid_edition.json') as grid_edition_file:
    grid_edition_data = json.load(grid_edition_file)
    release_date = grid_edition_data['edition']
    release_doi = grid_edition_data['doi']
    release_url = grid_edition_data['url']
    grid_wdid = grid_edition_data['edition_of_wdid']

grid_release = wdi_extension.MyRelease('GRID Release {0}'.format(release_date),
                                   '{0} release of the GRID database'.format(release_date), release_date,
                                   edition_of_wdid=grid_wdid,
                                   pub_date='+{0}T00:00:00Z'.format(release_date),
                                   url=release_url,
                                   doi=release_doi)

grid_release_item_id = grid_release.get_or_create(login_instance)

print('database edition item is {0}'.format(grid_release_item_id))

grid_data = grid_data.GridData('grid.json')
grid_data.load_country_map('country_map.csv')
grid_data.load_type_map('type_map.csv')

def create_grid_item(grid_data, grid_id, grid_release_item_id, login_instance):
    reference_info = [wdi_core.WDItemID(grid_release_item_id, 'P248', is_reference=True), wdi_core.WDExternalID(grid_id, p_grid_id, is_reference=True)]
    base_data = grid_data.base_data_for_id(grid_id)
    org_name = base_data['label']
    org_description = base_data['description']
    org_type_qid = base_data['type_qid']
    org_country_qid = base_data['country_qid']
    website = base_data['website']
    org_inception = base_data['inception']
    latitude = base_data['latitude']
    longitude = base_data['longitude']
    org_aliases = grid_data.aliases_for_id(grid_id)
    org_labels = grid_data.labels_for_id(grid_id)

    statements = []
    statements.append(wdi_core.WDItemID(org_type_qid, p_instance_of, references=[reference_info]))
    statements.append(wdi_core.WDExternalID(grid_id, p_grid_id, references=[reference_info]))
    if org_country_qid:
        statements.append(wdi_core.WDItemID(org_country_qid, p_country, references=[reference_info]))
    if website and (len(website) < 500):
        statements.append(wdi_core.WDUrl(website, p_official_website, references=[reference_info]))
    if org_inception and (int(org_inception) > 900):
        org_inception_date = datetime.date(int(org_inception), 1, 1)
        statements.append(wdi_core.WDTime(org_inception_date.strftime('+%Y-%m-%dT%H:%M:%SZ'), p_inception, precision=9,
                                          references=[reference_info])) # year-level precision in inception dates from GRID
    if latitude and longitude and (abs(latitude) <= 90.0) and (abs(longitude) <= 360.0):
        precision = 1.0
        longitude_parts = str(longitude).split('.')
        if len(longitude_parts) > 1:
            exp = len(longitude_parts[1])
            precision = pow(10.0, -exp)
        statements.append(wdi_core.WDGlobeCoordinate(float(latitude), float(longitude), precision,
                                                     p_coordinate_location, references=[reference_info]))
    wd_item = wdi_core.WDItemEngine(item_name=org_name,domain="organizations",data=statements)
    wd_item.set_label(label=org_name,lang='en')
    wd_item.set_description(description=org_description,lang='en')
    if org_aliases and len(org_aliases) > 0:
        wd_item.set_aliases(org_aliases, lang='en')
    for label_hash in org_labels:
        if label_hash['language'] == 'en':
            wd_item.set_aliases([label_hash['label']], 'en', append=True)
        else:
            wd_item.set_label(label=label_hash['label'], lang=label_hash['language'])
    new_item_id = wd_item.write(login_instance, edit_summary='Creating item from GRID record via APSbot_grid_create script (APSbot task 3)')
    print("created {0}".format(new_item_id))

entered_count = 0
min_entry = 1
max_entry = 40000
for grid_id in grid_data.valid_ids_not_in_wikidata():
    entered_count += 1
    print("{0} - {1}".format(entered_count, grid_id))
    if entered_count < min_entry:
        continue
    try:
        create_grid_item(grid_data, grid_id, grid_release_item_id, login_instance)
    except wdi_core.WDApiError as wd_error:
        print("Error creating GRID item for {0}: {1} - {2}".format(grid_id, sys.exc_info()[0], wd_error.wd_error_msg))
    except KeyError as key_error:
        print("Error creating GRID item for {0}: {1} - {2}".format(grid_id, sys.exc_info()[0], str(key_error)))
    except:
        print("Error creating GRID item for {0}: {1}".format(grid_id, sys.exc_info()[0]))
    if entered_count >= max_entry:
        break
