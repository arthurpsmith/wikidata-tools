from wikidataintegrator import wdi_core, wdi_login
import csv
import json
import wdi_extension

# Property values from live wikidata:
p_grid_id = 'P2427'

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


def create_grid_items(filename, grid_release_item_id, login_instance):
    reference_info = [wdi_core.WDItemID(grid_release_item_id, 'P248', is_reference=True)]
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            grid_id, org_name, org_description, org_type_qid, org_country_qid, website = row
            statements = []
            statements.append(wdi_core.WDItemID(org_type_qid, 'P31', references=[reference_info]))
            statements.append(wdi_core.WDExternalID(grid_id, 'P2427', references=[reference_info]))
            if org_country_qid:
                statements.append(wdi_core.WDItemID(org_country_qid, 'P17', references=[reference_info]))
            if website:
                statements.append(wdi_core.WDUrl(website, 'P856', references=[reference_info]))
            wd_item = wdi_core.WDItemEngine(item_name=org_name,domain="organizations",data=statements)
            wd_item.set_label(label=org_name,lang='en')
            wd_item.set_description(description=org_description,lang='en')
            wd_item.write(login_instance)


create_grid_items("grid_to_create.csv", grid_release_item_id, login_instance)