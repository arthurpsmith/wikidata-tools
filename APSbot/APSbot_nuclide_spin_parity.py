import pywikibot
import csv

# Property values from live wikidata:
p_stated_in = 'P248'
p_spin_quantum_number = 'P1122'
p_parity = 'P1123'
p_ref_url = 'P854'
p_retrieved = 'P813'
p_edition = 'P393'
nudat_qid = 'Q21234191'

retrieval_date = pywikibot.WbTime(year=2016, month=6, day=23)

precision = 10 ** -10

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()


def get_item(item_id):
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    return item


def check_claim(item, prop, value):
    """
    Requires a property and value and returns boolean.
    Returns the claim that fits into the defined precision or None.
    """
    item_dict = item.get()
    value = float(value)
    try:
        claims = item_dict['claims'][prop]
    except KeyError:
        return None

    claim_found = None
    for claim in claims:
        wb_quant = claim.getTarget()
        delta_amount = float(wb_quant.amount) - value
        if abs(delta_amount) < precision:
            claim_found = claim
    return claim_found


def check_source_set(claim, source_map):
    source_claims = claim.getSources()
    if len(source_claims) == 0:
        return False

    for source in source_claims:
        all_properties_present = True
        for prop in source_map.keys():
            target_type, source_value = source_map[prop]
            try:
                sources_with_property = source[prop]
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


def add_unitless_quantity(item, prop, data):
    value, uncert = data
    claim = pywikibot.Claim(repo, prop)
    wb_quant = pywikibot.WbQuantity(value, unit='1', error=uncert)
    claim.setTarget(wb_quant)
    item.addClaim(claim, bot=True, summary="Adding spin or parity claim from NNDC.")
    return claim


def create_source_claim(claim, source_map):
    source_claims = []
    for prop in source_map.keys():
        target_type, source_value = source_map[prop]
        source_claim = pywikibot.Claim(repo, prop, isReference=True)
        if target_type == 'item':
            source_page = pywikibot.ItemPage(repo, source_value)
            source_claim.setTarget(source_page)
        else:
            source_claim.setTarget(source_value)
        source_claims.append(source_claim)
    claim.addSources(source_claims, bot=True)
    return True


def check_and_add_entries(nuclide, name, prop, value, nndc_url):
    claim_to_update = check_claim(nuclide, prop, value)
    if claim_to_update is None:
        print('New value being added: {0} for {1}'.format(value, name))
        new_claim = add_unitless_quantity(nuclide, prop, [value, 0.0])
        source_map = {p_stated_in: ['item', nudat_qid],
                      p_edition: ['string', '2.6'],
                      p_ref_url: ['string', nndc_url],
                      p_retrieved: ['date', retrieval_date]}
        print('Add source: {0}'.format(nndc_url))
        create_source_claim(new_claim, source_map)
    else:
        source_map = {p_stated_in: ['item', nudat_qid],
                      p_edition: ['string', '2.6'],
                      p_ref_url: ['string', nndc_url]}
        if not check_source_set(claim_to_update, source_map):
            print('Add source: {0}'.format(nndc_url))
            source_map[p_retrieved] = ['date', retrieval_date]
            create_source_claim(claim_to_update, source_map)


def process_spin_parity_data(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            nuclide_qid, spin, parity, nuclide_name, nndc_url = row
            nuclide = get_item(nuclide_qid)
            check_and_add_entries(nuclide, nuclide_name, p_spin_quantum_number, float(spin), nndc_url)
            check_and_add_entries(nuclide, nuclide_name, p_parity, int(parity), nndc_url)

process_spin_parity_data('spin_parity_data.csv')
