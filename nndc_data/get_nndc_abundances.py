#
import nuclides
import nndc_data
import math
import sys

#

nuclide_provider_class = nuclides.SparqlNuclideProvider

nuclide_provider = nuclide_provider_class()

nuclides = nuclide_provider.get_nuclides()

nuclides_by_protons_neutrons = {}
for nuclide in nuclides:
    nuclides_by_protons_neutrons['{}_{}'.format(nuclide.atomic_number, nuclide.neutron_number)] = nuclide.item_id

# Should filter out where nuclides data already includes this value...

for nuclide in nuclides:
    z = nuclide.atomic_number
    n = nuclide.neutron_number
    abundance, uncertainty, source_url = nndc_data.nndc_abundance(z, n)
    if abundance != None :
        print(u"{0},{1},{2},{3},{4}".format(nuclide.item_id,
            abundance, uncertainty, nuclide.label, source_url))
