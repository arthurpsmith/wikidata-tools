# -*- coding: utf-8 -*-
#
import nuclides
import nndc_data
import codecs
import sys

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

nuclide_provider_class = nuclides.WdqNuclideProvider

nuclide_provider = nuclide_provider_class('en')

nuclides = nuclide_provider.get_nuclides()


# Should filter out half_life = None, STABLE, or where
# nuclides data already includes this value

for nuclide in nuclides:
    half_life, half_life_unit, uncertainty, source_url = nndc_data.nndc_half_life(
        nuclide.atomic_number, nuclide.neutron_number)
    # Fix very small amounts listed as xxe-18 or lower s:
    if ((half_life_unit == 's') and (half_life < 1.0e-15)):
        half_life_unit = 'as'
        half_life *= 1.0e18
        uncertainty *= 1.0e18
        
    time_unit_qid = nndc_data.nndc_time_id(half_life_unit)
    print u"{0},{1},{2},{3},{4},{5},{6}".format(nuclide.item_id,
        half_life, uncertainty, time_unit_qid, half_life_unit,
        nuclide.label, source_url)
