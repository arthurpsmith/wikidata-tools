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
            if '.' in hl_string:
                digits = 0
                expt = 0
                m2 = re.search(r'\.(\d+)E([-\+]?\d+)$', hl_string)
                if m2 is None:
                    parts = hl_string.split('.')
                    digits = len(parts[1])
                else:
                    digits = len(m2.group(1))
                    expt = int(m2.group(2))
                unc_factor = 10.0 ** (expt - digits)

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
