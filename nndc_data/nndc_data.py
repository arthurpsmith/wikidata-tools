#
# -*- coding: utf-8 -*-

from lxml import html
import requests
import re

nndc_url = 'http://www.nndc.bnl.gov/nudat2/reCenter.jsp'

time_units_to_qids = {
    's': 'Q11574',        # second
    'm': 'Q7727',         # minute
    'h': 'Q25235',        # hour
    'd': 'Q573',          # day
    'y': 'Q1092296',      # year (annum)
    'ms': 'Q723733',      # millisecond
    'µS': 'Q842015',      # microsecond
    u'\xb5S': 'Q842015',      # microsecond unicode encoding
    'ns': 'Q838801',      # nanosecond
    'ps': 'Q3902709',     # picosecond
    'fs': 'Q1777507',     # femtosecond
    'as': 'Q2483628'      # attosecond
}

def nndc_time_id(time_unit):
    qid = None
    if time_unit in time_units_to_qids:
        qid = time_units_to_qids[time_unit]
    return qid


decay_modes_to_qids = {
    u'\u03b2-': 'Q14646001',  # beta minus decay
    u'2\u03b2-': 'Q18907407',   # double beta - decay
    u'\u03b2+': 'Q1357356',    # positron emission (beta plus)
    u'\u03b5': 'Q109910',     # electron capture
    u'2\u03b5': 'Q520827',    # double electron capture
    u'\u03b1': 'Q179856',     # alpha decay
    'n': 'Q898923',           # neutron emission
    'p': 'Q902157',           # proton emission
    'SF': 'Q146682',          # spontaneous fission
    '2p': 'Q9253686',         # 2-proton decay
    '2n': 'Q21456752',        # 2-neutron decay
    u'\u03b2-n': 'Q14646001|Q898923',  # beta minus + neutron decay
    u'\u03b2-2n': 'Q14646001|Q21456752',  # beta minus + 2 neutron decay
    u'\u03b2-3n': 'Q14646001|Q21457084',  # beta minus + 3 neutron decay
    u'\u03b2-4n': 'Q14646001|Q21457201',  # beta minus + 4 neutron decay
    u'\u03b2-\u03b1': 'Q14646001|Q179856',  # beta minus + alpha decay
    u'\u03b2-n\u03b1': 'Q14646001|Q898923|Q179856',  # beta minus + neutron + alpha decay
    u'\u03b5\u03b1': 'Q109910|Q179856',     # electron capture + alpha
    u'\u03b5p': 'Q109910|Q902157',     # electron capture + proton emission
    u'\u03b52p': 'Q109910|Q9253686',     # electron capture + 2 proton emission
    u'\u03b53p': 'Q109910|Q21457313',     # electron capture + 3 proton emission
    u'2\u03b1': 'Q21457421'     # double alpha emission
}

decay_mode_nucleon_changes = {
    'Q14646001': [+1, -1],    # beta minus decay - n -> p + e-
    'Q901747': [+2, -2],      # double beta - 2 n -> 2 p + 2 e-
    'Q1357356': [-1, +1],     # positron emission - p -> n + e+
    'Q109910': [-1, +1],      # electron capture - e- + p -> n
    'Q520827': [-2, +2],      # double e cap - 2e- + 2p -> 2n
    'Q179856': [-2, -2],      # alpha decay
    'Q898923': [0, -1],       # neutron emission
    'Q902157': [-1, 0],       # proton emission
    'Q9253686': [-2, 0],     # 2-proton emission
    'Q21457313': [-3, 0],     # 3-proton emission
    'Q21456752': [0, -2],     # 2-neutron emission
    'Q21457084': [0, -3],     # 3-neutron emission
    'Q21457201': [0, -4],     # 4-neutron emission
    'Q21457421': [-4, -4]     # double alpha decay
}


def nndc_decay_id(decay_mode):
    qid = None
    if decay_mode in decay_modes_to_qids:
        qid = decay_modes_to_qids[decay_mode]
    return qid


def protons_neutrons_after_decay(protons, neutrons, decay_mode_qid):
    if decay_mode_qid is None:
        return None

    qids_to_use = [decay_mode_qid]
    if '|' in decay_mode_qid:
        qids_to_use = decay_mode_qid.split('|')
        
    for dm_qid in qids_to_use:
        if dm_qid in decay_mode_nucleon_changes:
            change = decay_mode_nucleon_changes[dm_qid]
        else: # Unknown (SF can have many products)
           return None
        protons += change[0]
        neutrons += change[1]

    return [protons, neutrons]

def lowest_increment_of_float_string(fl_string):
    unc_factor = 1.0
    if '.' in fl_string:
        digits = 0
        expt = 0
        m2 = re.search(r'\.(\d+)E([-\+]?\d+)$', fl_string)
        if m2 is None:
            parts = fl_string.split('.')
            digits = len(parts[1])
        else:
            digits = len(m2.group(1))
            expt = int(m2.group(2))
        unc_factor = 10.0 ** (expt - digits)
    return unc_factor


# Note uncertainty in NDS style means in last significant digit
# eg. 4.623 3 => uncertainty is 0.003 (1-sigma)

def nndc_half_life(protons, neutrons):
    query = {'z':protons, 'n':neutrons}
    page = requests.get(nndc_url, params=query)
    query_url = page.url
    tree = html.fromstring(page.text)

    half_life = None
    half_life_unit = None
    unc = None

    nuclide_data_rows = tree.xpath('//tr[@class="cp"]')
    for row in nuclide_data_rows:
        entries = row.getchildren()
        level = entries[0].text_content()
        if (level == '0.0'):
            half_life = entries[3].text
            if len(entries[3].getchildren()) > 0:
                unc = entries[3].getchildren()[0].text

    unc_factor = 1.0
    if half_life is not None:
        m = re.search(r'([-\d\.E\+]+)\s+(\S+)\s*$', half_life, re.UNICODE)
        if m is not None:
            hl_string = m.group(1)
            half_life_unit = m.group(2)
            half_life = float(hl_string)
            unc_factor = lowest_increment_of_float_string(hl_string)

    if unc is not None:
        m = re.match(r'^\+([\d\.]+)\-([\d\.]+)$', unc)
        if m is None:
            m2 = re.match(r'^\-([\d\.]+)\+([\d\.]+)$', unc)
            if m2 is None:
                unc = float(unc) * unc_factor
            else:
                lower_unc = float(m2.group(1))
                upper_unc = float(m2.group(2))
                unc = max(upper_unc, lower_unc) * unc_factor
        else:
            upper_unc = float(m.group(1))
            lower_unc = float(m.group(2))
            unc = max(upper_unc, lower_unc) * unc_factor # would be better to show true bounds
    return half_life, half_life_unit, unc, query_url

# 

def nndc_decay_modes(protons, neutrons):
    query = {'z':protons, 'n':neutrons}
    page = requests.get(nndc_url, params=query)
    query_url = page.url
    tree = html.fromstring(page.text)

    decay_modes = []

    decay_modes_string = None
    nuclide_data_rows = tree.xpath('//tr[@class="cp"]')
    for row in nuclide_data_rows:
        entries = row.getchildren()
        level = entries[0].text_content()
        # Note: decay modes is last column; may be 5th or 6th (if abundance listed)
        if (level == '0.0'):
            decay_modes_string = entries[-1].text_content()

    if decay_modes_string is None:
        return [], query_url

    decay_modes_parts = decay_modes_string.split(' ')
    current_mode = None
    for part in decay_modes_parts:
        if part == '' or part == '%' or part == ':' or part == '<' or part == '>':
            continue
        if part == u'\u2264' or part == u'\u2265' or part == u'\u2248': # >= or <= or approx
            continue
        m = re.match(r'\d+\.?\d*[-E\d]*$', part)
        if m is None:
            if current_mode is not None:
                decay_modes.append({'mode':current_mode})
            current_mode = part
        else:
            pct = float(part)
            decay_modes.append({'mode':current_mode, 'pct':pct})
            current_mode = None
    if current_mode is not None:
         decay_modes.append({'mode':current_mode})
    return decay_modes, query_url

def nndc_abundance(protons, neutrons):
    query = {'z':protons, 'n':neutrons}
    page = requests.get(nndc_url, params=query)
    query_url = page.url
    tree = html.fromstring(page.text)

    abundance_str = None
    abundance = None
    uncertainty = None

    nuclide_data_rows = tree.xpath('//tr[@class="cp"]')
    for row in nuclide_data_rows:
        entries = row.getchildren()
    # Note: abundance is 5th column, but only if 6 columns present
        if len(entries) == 6:
            level = entries[0].text_content()
            if (level == '0.0'):
                abundance_str = entries[4].text
                if '%' in abundance_str:
                    abundance_str = re.sub('%\s*$', '', abundance_str)
                    abundance = float(abundance_str)*0.01 # expressed as %
                    if len(entries[4].getchildren()) > 0:
                        uncertainty = 0.01*float(entries[4].getchildren()[0].text)
    if abundance != None and uncertainty != None:
        unc_factor = lowest_increment_of_float_string(abundance_str)
        uncertainty = uncertainty * unc_factor

    return abundance, uncertainty, query_url
