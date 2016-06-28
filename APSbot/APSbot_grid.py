import pywikibot
import csv

# Property values from live wikidata:
p_grid_id = 'P2427'
p_doi = 'P356'
p_edition = 'P393'
p_ref_url = 'P854'

retrieval_date = pywikibot.WbTime(year=2016, month=5, day=31)
source_doi = '10.6084/m9.figshare.3409414'
reference_url = 'https://figshare.com/articles/GRID_release_2016-05-31/3409414'
edition = '2016-05-31'

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()


def get_item(item_id):
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    return item


def check_claim(item, prop, target):
    """
    Requires a property, value, uncertainty and unit and returns boolean.
    Returns the claim that fits into the defined precision or None.
    """
    item_dict = item.get()
    try:
        claims = item_dict['claims'][prop]
    except KeyError:
        return None

    for claim in claims:
        if claim.target_equals(target):
            return claim
    return None


def check_source_set(claim, source_map):
    source_claims = claim.getSources()
    if len(source_claims) == 0:
        return False

    for source in source_claims:
        all_properties_present = True
        for src_prop in source_map.keys():
            target_type, source_value = source_map[src_prop]
            try:
                sources_with_property = source[src_prop]
            except KeyError:
                continue
            found = False
            if target_type == 'item':
                found = source_value in map(lambda src: src.target.id, sources_with_property)
            elif target_type == 'string':
                found = source_value in map(lambda src: src.target, sources_with_property)
            if not found:
                all_properties_present = False
                break
        if all_properties_present:
            return True
    return False


def add_string_claim(item, prop, str_value):
    claim = pywikibot.Claim(repo, prop)
    claim.setTarget(str_value)
    item.addClaim(claim, bot=True, summary="Adding GRID identifier.")
    return claim


def create_source_claim(claim, source_map):
    source_claims = []
    for src_prop in source_map.keys():
        target_type, source_value = source_map[src_prop]
        source_claim = pywikibot.Claim(repo, src_prop, isReference=True)
        if target_type == 'item':
            source_page = pywikibot.ItemPage(repo, source_value)
            source_claim.setTarget(source_page)
        else:
            source_claim.setTarget(source_value)
        source_claims.append(source_claim)
    claim.addSources(source_claims, bot=True)
    return True


def process_grid_data(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            grid_id, org_qid, org_name = row
            organization = get_item(org_qid)
            grid_claim = check_claim(organization, p_grid_id, grid_id)
            if grid_claim is None:
                print('New entry: {0} for {1} ({2})'.
                      format(grid_id, org_qid, org_name))
                new_claim = add_string_claim(organization, p_grid_id, grid_id)
                source_map = {p_doi: ['string', source_doi],
                              p_edition: ['string', edition],
                              p_ref_url: ['string', reference_url]}
                print('Add source: {0}'.format(source_doi))
                create_source_claim(new_claim, source_map)
            else:
                source_map = {p_doi: ['string', source_doi],
                              p_edition: ['string', edition],
                              p_ref_url: ['string', reference_url]}
                if not check_source_set(grid_claim, source_map):
                    create_source_claim(grid_claim, source_map)


process_grid_data('grid_wikidata.csv')
