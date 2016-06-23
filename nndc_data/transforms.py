import nndc_data
import math
from fractions import Fraction
from units import time_in_seconds

# See http://www.nndc.bnl.gov/chart/help/glossary.jsp#halflife
# Using formula half-life = ln(2) x h/2pi / Gamma (for line-width Gamma)
# Then for the following definitions,
#   half-life = planck_ratio/Gamma in attoseconds where Gamma is in eV
#
Planck_h = 4.135667662e-15  # Units of eV s
planck_ratio = math.log(2.0) * Planck_h * 1.0e18 / (2 * math.pi)


def half_life_values(hl_hash):
    half_life_unit = hl_hash['unit']
    half_life = hl_hash['value']
    uncertainty = hl_hash['uncertainty']

    # Fix very small amounts listed as xxe-18 or lower s:
    if (half_life_unit == 's') and (half_life < 1.0e-15):
        half_life_unit = 'as'
        half_life *= 1.0e18
        if uncertainty is not None:
            uncertainty *= 1.0e18

    if half_life_unit == 'eV':
        half_life_unit = 'as'
        new_half_life = planck_ratio / (1.0 * half_life)
        if uncertainty is not None:
            uncertainty *= new_half_life / half_life
        half_life = new_half_life
    if half_life_unit == 'keV':
        half_life_unit = 'as'
        new_half_life = planck_ratio / (1000.0 * half_life)
        if uncertainty is not None:
            uncertainty *= new_half_life / half_life
        half_life = new_half_life
    if half_life_unit == 'MeV':
        half_life_unit = 'as'
        new_half_life = planck_ratio / (1.0e6 * half_life)
        if uncertainty is not None:
            uncertainty *= new_half_life / half_life
        half_life = new_half_life

    time_unit_qid = nndc_data.nndc_time_id(half_life_unit)

    return half_life, uncertainty, time_unit_qid, half_life_unit


def decay_mode_values(dm_hash, z, n, nuclides_by_protons_neutrons):
    mode = dm_hash['mode']
    mode_qid = nndc_data.nndc_decay_id(mode)
    mode_qid_num = None
    if (mode_qid is not None) and ('|' not in mode_qid):  # unrecognized or multi-step decay mode
        mode_qid_num = int(mode_qid.replace('Q', ''))
    pct = None
    if 'pct' in dm_hash:
        pct = dm_hash['pct']
    pn = nndc_data.protons_neutrons_after_decay(z, n, mode_qid)
    if pn is not None:
        key = '{}_{}'.format(pn[0], pn[1])
        if key in nuclides_by_protons_neutrons:
            decays_to = nuclides_by_protons_neutrons[key]
        else:
            decays_to = None
    else:
        decays_to = None
    return mode, mode_qid, mode_qid_num, pct, decays_to


def spin_parity_values(spin_string, parity_string):
    spin = None
    parity = None
    if spin_string is not None:
        spin = float(Fraction(spin_string))
    if parity_string is not None:
        parity = int(parity_string)
    return spin, parity


def abundance_values(ab_hash):
    abundance = None
    uncertainty = None
    if ab_hash is not None:
        abundance = ab_hash['value']
        uncertainty = ab_hash['uncertainty']
    return abundance, uncertainty


def float_values_differ(a, b):
    differ = True
    if a is None:
        if b is None:
            differ = False
    else:
        if b is not None:
            if abs(a - b) < 1.0e-6:
                differ = False
    return differ


def timespans_differ(time_quantity, time_unit_qid, b_seconds):
    differ = True
    if time_quantity is None:
        if b_seconds is None:
            differ = False
    else:
        if b_seconds is not None:
            a_seconds = time_in_seconds(time_quantity, time_unit_qid)
            diff = abs(a_seconds - b_seconds)
            if diff <= 1.0e-6 * b_seconds:
                differ = False
    return differ
