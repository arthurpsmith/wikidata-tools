import pywikibot
import csv
from pywikibot.data import api

# Property values from live wikidata:
p_stated_in = 'P248'
p_retrieved = 'P813'
p_edition = 'P393'
p_ref_url = 'P854'
p_decays_to = 'P816'
p_decay_mode = 'P817'
p_proportion = 'P1107'
nudat_qid = 'Q21234191'

retrieval_date = pywikibot.WbTime(year=2015, month=11, day=9)

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()


def get_item(id):
    item = pywikibot.ItemPage(repo, id)
    item.get()
    return item


def get_claim_with_qualifiers(item, property, target, qualifiers):
    """
    Requires a property, item, and list of qualifier properties and items.
    Returns claim that matches or None.
    """
    item_dict = item.get()
    try:
        claims = item_dict['claims'][property]
    except:
        return None

    claim_exists = False
    for claim in claims:
        if not claim.target_equals(target):
            continue
        qual_missing = False
        for qual in qualifiers:
            if not claim.has_qualifier(qual[0], qual[1]):
                qual_missing = True
                continue
        if not qual_missing:
            return claim
    return None

def check_or_fix_proportion(claim, pct):
    fraction = pct * 0.01
    prop_qual = None
    for qualifier in claim.qualifiers.get(p_proportion, []):
        wb_quant = qualifier.getTarget()
        if fraction >= wb_quant.lowerBound and fraction <= wb_quant.upperBound:
            return True
        prop_qual = qualifier

    wb_quant = pywikibot.WbQuantity(fraction, unit = '1', error = 0.0)
    if prop_qual is None: # Add new qualifier
        prop_qual = pywikibot.Claim(repo, p_proportion)
        prop_qual.setTarget(wb_quant)
        claim.addQualifier(prop_qual, bot=True, summary="Adding branching fraction qualifier from NNDC.")
    else: # Modify target value:
        prop_qual.changeTarget(wb_quant)
    
    return False

def check_source_set(claim, source_map):
    source_claims = claim.getSources()
    if len(source_claims) == 0:
        return False

    for source in source_claims:
        all_properties_present = True
        for property in source_map.keys():
            target_type, source_value = source_map[property]
            try:
                sources_with_property = source[property]
            except:
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


def add_decay_claim(item, decay_to_qid, decay_mode_qid, pct):
    claim = pywikibot.Claim(repo, p_decays_to)
    target_page = pywikibot.ItemPage(repo, decay_to_qid)
    claim.setTarget(target_page)

    decay_mode_page = pywikibot.ItemPage(repo, decay_mode_qid)
    qual_mode = pywikibot.Claim(repo, p_decay_mode)
    qual_mode.setTarget(decay_mode_page)
    claim.addQualifier(qual_mode)

    qual_frac = pywikibot.Claim(repo, p_proportion)
    wb_quant = pywikibot.WbQuantity(0.01 * pct, unit = '1', error = 0.0)
    qual_frac.setTarget(wb_quant)
    claim.addQualifier(qual_frac)

    item.addClaim(claim, bot=True, summary="Adding decay mode claim from NNDC.")
    return claim


def create_source_claim(claim, source_map):
    source_claims = []
    for property in source_map.keys():
        target_type, source_value = source_map[property]
        source_claim = pywikibot.Claim(repo, property, isReference=True)
        if (target_type == 'item'):
            source_page = pywikibot.ItemPage(repo, source_value)
            source_claim.setTarget(source_page)
        else:
            source_claim.setTarget(source_value)
        source_claims.append(source_claim)
    claim.addSources(source_claims, bot=True)
    return True

def process_nndc_data(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            nuclide_qid, decay_mode, decay_mode_qid, pct, decay_to_qid, nuclide_name, nndc_url = row
            if pct == 'None':
                pct = None
            else:
                pct = float(pct)
            print('checking: {0}->{1} via {2} ({3}%) - {4}'.format(
                    nuclide_qid, decay_to_qid, decay_mode_qid, pct, nuclide_name))
            nuclide = get_item(nuclide_qid)
            decay_claim = get_claim_with_qualifiers(nuclide, p_decays_to, decay_to_qid, [[p_decay_mode, decay_mode_qid]])
            if (decay_claim is None):
                print('New entry: {0}->{1} via {2} ({3}) - {4}'.format(
                    nuclide_qid, decay_to_qid, decay_mode_qid, pct, nuclide_name))
                new_claim = add_decay_claim(nuclide, decay_to_qid, decay_mode_qid, pct)
                source_map = {p_stated_in: ['item', nudat_qid],
                          p_edition: ['string', '2.6'],
                          p_ref_url: ['string', nndc_url],
                          p_retrieved: ['date', retrieval_date]}
                print('Add source: {0}'.format(nndc_url))
                create_source_claim(new_claim, source_map)
            else:
                print('Found claim!: {0}'.format(decay_claim))
                if pct != 'None':
                    check_or_fix_proportion(decay_claim, pct)
                source_map = {p_stated_in: ['item', nudat_qid],
                          p_edition: ['string', '2.6'],
                          p_ref_url: ['string', nndc_url]}
                if not check_source_set(decay_claim, source_map):
                    source_map[p_retrieved] = ['date', retrieval_date]
                    create_source_claim(decay_claim, source_map)

process_nndc_data('test2.csv')
