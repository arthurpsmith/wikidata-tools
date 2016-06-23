#
import nuclides
import nndc_data
import transforms

#

nuclide_provider_class = nuclides.SparqlNuclideProvider

nuclide_provider = nuclide_provider_class()

nuclides = nuclide_provider.get_nuclides()

nuclides_by_protons_neutrons = {}
for nuclide in nuclides:
    if nuclide.isomer_index == 0:
        nuclides_by_protons_neutrons['{}_{}'.format(nuclide.atomic_number, nuclide.neutron_number)] = nuclide.item_id

# Only write out entries where the data is missing on the wikidata side - or otherwise different...
half_life_file = open('half_life_data.csv', 'w')
decays_file = open('decays_data.csv', 'w')
spin_parity_file = open('spin_parity_data.csv', 'w')
abundance_file = open('abundance_data.csv', 'w')

for nuclide in nuclides:
    z = nuclide.atomic_number
    n = nuclide.neutron_number
    ii = nuclide.isomer_index
    nndc_nuclide = nndc_data.all_nuclide_data(z, n, ii)
    if len(nndc_nuclide) == 0:
        print("Warning: No data found from NNDC for Z={0} N={1} II={2}".format(z, n, ii))
        continue
    half_life, hl_unc, time_unit_qid, time_unit_label = transforms.half_life_values(nndc_nuclide['half_life'])
    if (time_unit_qid is not None) and (transforms.timespans_differ(half_life, time_unit_qid, nuclide.half_life)):
        half_life_file.write("{0},{1},{2},{3},{4},{5},{6}\n".
                             format(nuclide.item_id, half_life, hl_unc, time_unit_qid, time_unit_label,
                                    nuclide.label, nndc_nuclide['source_url']))

    for decay_mode in nndc_nuclide['decay_modes']:
        mode, mode_qid, mode_qid_num, pct, decays_to = transforms.decay_mode_values(decay_mode, z, n,
                                                                                    nuclides_by_protons_neutrons)
        if mode_qid_num not in nuclide.decay_modes:
            decays_file.write("{0},{1},{2},{3},{4},{5},{6}\n".
                              format(nuclide.item_id, mode, mode_qid, pct, decays_to,
                                     nuclide.label, nndc_nuclide['source_url']))

    spin, parity = transforms.spin_parity_values(nndc_nuclide['spin'], nndc_nuclide['parity'])
    if (spin != nuclide.spin) or (parity != nuclide.parity):
        spin_parity_file.write("{0},{1},{2},{3},{4}\n".
                               format(nuclide.item_id, spin, parity, nuclide.label, nndc_nuclide['source_url']))

    abundance, ab_unc = transforms.abundance_values(nndc_nuclide['abundance'])
    if transforms.float_values_differ(abundance, nuclide.abundance):
        abundance_file.write("{0},{1},{2},{3},{4}\n".
                             format(nuclide.item_id, abundance, ab_unc, nuclide.label, nndc_nuclide['source_url']))

half_life_file.close()
decays_file.close()
spin_parity_file.close()
abundance_file.close()
