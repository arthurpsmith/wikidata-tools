# -*- coding: utf-8 -*-
#
import nuclides
import nndc_data
import math

# See http://www.nndc.bnl.gov/chart/help/glossary.jsp#halflife
# Using formula half-life = ln(2) x h/2pi / Gamma (for line-width Gamma)
# Then for the following definitions, 
#   half-life = planck_ratio/Gamma in attoseconds where Gamma is in eV
#
Planck_h = 4.135667662e-15  # Units of eV s
planck_ratio = math.log(2.0)*Planck_h*1.0e18/(2*math.pi)

nuclide_provider_class = nuclides.SparqlNuclideProvider

nuclide_provider = nuclide_provider_class()

nuclides = nuclide_provider.get_nuclides()


# Should filter out half_life = None, STABLE, or where
# nuclides data already includes this value

for nuclide in nuclides:
    nuclide_data = nndc_data.all_nuclide_data(nuclide.atomic_number, nuclide.neutron_number, nuclide.isomer_index)
    half_life = nuclide_data['half_life']['value']
    half_life_unit = nuclide_data['half_life']['unit']
    uncertainty = nuclide_data['half_life']['uncertainty']
    source_url = nuclide_data['source_url']
    # Fix very small amounts listed as xxe-18 or lower s:
    if (half_life_unit == 's') and (half_life < 1.0e-15):
        half_life_unit = 'as'
        half_life *= 1.0e18
        if uncertainty is not None:
            uncertainty *= 1.0e18

    if half_life_unit == 'eV':
        half_life_unit = 'as'
        new_half_life = planck_ratio/(1.0*half_life)
        if uncertainty is not None:
            uncertainty *= new_half_life/half_life
        half_life = new_half_life
    if half_life_unit == 'keV':
        half_life_unit = 'as'
        new_half_life = planck_ratio/(1000.0*half_life)
        if uncertainty is not None:
            uncertainty *= new_half_life/half_life
        half_life = new_half_life
    if half_life_unit == 'MeV':
        half_life_unit = 'as'
        new_half_life = planck_ratio/(1.0e6*half_life)
        if uncertainty is not None:
            uncertainty *= new_half_life/half_life
        half_life = new_half_life
        
    time_unit_qid = nndc_data.nndc_time_id(half_life_unit)
    print(u"{0},{1},{2},{3},{4},{5},{6}".
          format(nuclide.item_id,
                 half_life, uncertainty, time_unit_qid, half_life_unit,
                 nuclide.label, source_url))
