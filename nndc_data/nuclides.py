#
# Stripped down from wikidata periodic table (chemistry.py originally)
#
import json
import operator
import re
from units import time_in_seconds
from urllib.parse import urlencode
from urllib.request import urlopen
from collections import defaultdict


def get_json_with_get(url, url_encoded_params):
    """Get rather than Post request - information is cached for 6 hours."""
    with urlopen("{0}?{1}".format(url, url_encoded_params)) as response:
        raw = response.read()
    return json.loads(raw.decode('utf-8'))


class SparqlBase:
    """Load items from Wikidata SPARQL query service."""

    SPARQL_API = 'https://query.wikidata.org/sparql'

    @classmethod
    def get_sparql(cls, query):
        response = get_json_with_get(cls.SPARQL_API,
                                     urlencode({'query': query,
                                                'format': 'json'}))
        return response['results']['bindings']


class NuclideProvider(object):
    """Base class for nuclide providers."""

    def iter_good(self):
        iterator = iter(self)
        while True:
            try:
                yield next(iterator)
            except StopIteration:
                raise

    def get_nuclides(self):
        nuclides = []
        lastanum = -1
        lastnnum = -1
        for nuclide in self.iter_good():
            if nuclide.atomic_number is not None and nuclide.neutron_number is not None:
                if nuclide.atomic_number > lastanum:
                    lastanum = nuclide.atomic_number
                if nuclide.neutron_number > lastnnum:
                    lastnnum = nuclide.neutron_number
                nuclides.append(nuclide)
        nuclides.sort(key=operator.attrgetter('atomic_number',
                                              'neutron_number',
                                              'isomer_index'))
        return nuclides


# No longer filtering out isomers...
class SparqlNuclideProvider(SparqlBase, NuclideProvider):
    """Load nuclide info from Wikidata Sparql endpoint."""
    def __iter__(self):
        nuclides = defaultdict(Nuclide)
        nuclides_query = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> \
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \
PREFIX wd: <http://www.wikidata.org/entity/> \
SELECT ?nuclide ?atomic_number ?neutron_number ?label WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             wdt:P{3} ?atomic_number ; \
             wdt:P{4} ?neutron_number ; \
             rdfs:label ?label . \
    FILTER(lang(?label) = 'en') \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
            Nuclide.atomic_number_pid, Nuclide.neutron_number_pid)
        query_result = self.get_sparql(nuclides_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            atomic_number = nuclide_result['atomic_number']['value']
            neutron_number = nuclide_result['neutron_number']['value']
            label = nuclide_result['label']['value']
            nuclides[nuclide_uri].atomic_number = int(atomic_number)
            nuclides[nuclide_uri].neutron_number = int(neutron_number)
            nuclides[nuclide_uri].label = label
            nuclides[nuclide_uri].half_life = None
            nuclides[nuclide_uri].item_id = nuclide_uri.split('/')[-1]
            isomer_string_match = re.search('-\d+m(\d*)', label)
            if isomer_string_match:
                if isomer_string_match.group(1) == '':
                    nuclides[nuclide_uri].isomer_index = 1
                else:
                    nuclides[nuclide_uri].isomer_index = int(isomer_string_match.group(1))
            else:
                special_match = re.search('-\d+([ab])', label)  # this is used in at least one case where level order is unknown
                if special_match:
                    if special_match.group(1) == 'b':
                        nuclides[nuclide_uri].isomer_index = 2
                    else:
                        nuclides[nuclide_uri].isomer_index = 1
                else:
                    nuclides[nuclide_uri].isomer_index = 0

        stable_query = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> \
PREFIX wd: <http://www.wikidata.org/entity/> \
SELECT ?nuclide WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             wdt:P{0} wd:Q{3} . \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
            Nuclide.stable_qid)
        query_result = self.get_sparql(stable_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            if nuclide_uri in nuclides:
                nuclides[nuclide_uri].classes.append('stable')

        hl_query = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> \
PREFIX wd: <http://www.wikidata.org/entity/> \
PREFIX wikibase: <http://wikiba.se/ontology#> \
PREFIX psv: <http://www.wikidata.org/prop/statement/value/> \
PREFIX p: <http://www.wikidata.org/prop/> \
SELECT ?nuclide ?half_life ?half_life_unit WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             p:P{3} ?hl_statement . \
    ?hl_statement psv:P{3} ?hl_value . \
    ?hl_value wikibase:quantityAmount ?half_life ; \
              wikibase:quantityUnit ?half_life_unit . \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
            Nuclide.half_life_pid)

        query_result = self.get_sparql(hl_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            if nuclide_result['half_life']['value'] == '0':
                continue  # WDQS bug: values sometimes zero - skip
            if nuclide_uri in nuclides:
                if nuclides[nuclide_uri].half_life is None:
                    nuclides[nuclide_uri].half_life = time_in_seconds(
                        nuclide_result['half_life']['value'],
                        nuclide_result['half_life_unit']['value'])
                # else - sparql returned more than 1 half-life value - problem?

        decay_query = "PREFIX ps: <http://www.wikidata.org/prop/statement/> \
PREFIX pq: <http://www.wikidata.org/prop/qualifier/> \
PREFIX p: <http://www.wikidata.org/prop/> \
PREFIX wdt: <http://www.wikidata.org/prop/direct/> \
PREFIX wd: <http://www.wikidata.org/entity/> \
SELECT ?nuclide ?decay_to ?decay_mode ?fraction WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             p:P{3} ?decay_statement . \
    ?decay_statement ps:P{3} ?decay_to ; \
                     pq:P{4} ?decay_mode ; \
                     pq:P{5} ?fraction . \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
            Nuclide.decays_to_pid, Nuclide.decay_mode_pid,
            Nuclide.proportion_pid)
        query_result = self.get_sparql(decay_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            if nuclide_uri in nuclides:
                decay_mode_uri = nuclide_result['decay_mode']['value']
                decay_mode = int(decay_mode_uri.split('/')[-1].replace('Q', ''))
                nuclides[nuclide_uri].decay_modes.append(decay_mode)

        spin_parity_query = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> \
PREFIX wd: <http://www.wikidata.org/entity/> \
SELECT ?nuclide ?spin ?parity WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             wdt:P{3} ?spin ; \
             wdt:P{4} ?parity . \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
           Nuclide.spin_pid, Nuclide.parity_pid)

        query_result = self.get_sparql(spin_parity_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            if nuclide_uri in nuclides:
                spin = nuclide_result['spin']['value']
                parity = nuclide_result['parity']['value']
                nuclides[nuclide_uri].spin = float(spin)
                nuclides[nuclide_uri].parity = int(parity)

        abundance_query = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> \
PREFIX wd: <http://www.wikidata.org/entity/> \
SELECT ?nuclide ?abundance WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             wdt:P{3} ?abundance . \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
                   Nuclide.abundance_pid)

        query_result = self.get_sparql(abundance_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            if nuclide_uri in nuclides:
                abundance = nuclide_result['abundance']['value']
                nuclides[nuclide_uri].abundance = float(abundance)

        for item_id, nuclide in nuclides.items():
            yield nuclide


class PropertyAlreadySetException(Exception):
    """Property already set."""


class Nuclide(object):

    props = ('atomic_number', 'neutron_number', 'item_id', 'label',
             'half_life', 'decay_modes', 'spin', 'parity', 'level_energy',
             'isomer_index', 'abundance')
    atomic_number_pid = 1086
    neutron_number_pid = 1148
    half_life_pid = 2114
    decays_to_pid = 816
    decay_mode_pid = 817
    proportion_pid = 1107
    instance_pid = 31
    subclass_pid = 279
    isotope_qid = 25276  # top-level class under which all isotopes to be found
    stable_qid = 878130  # id for stable isotope
    isomer_qid = 846110  # metastable isomers all instances of this
    spin_pid = 1122  # Value is numeric - 0.5, 1.0, etc. no units
    parity_pid = 1123  # Value should be 1 or -1
    binding_energy_pid = 2154
    abundance_pid = 2374

    def __init__(self, **kwargs):
        self.decay_modes = []
        self.spin = None
        self.parity = None
        self.abundance = None
        for key, val in kwargs.items():
            if key in self.props:
                setattr(self, key, val)
        self.classes = []

    def __setattr__(self, key, value):
        if (key in self.props and hasattr(self, key) and
                getattr(self, key) is not None and getattr(self, key) != value):
            raise PropertyAlreadySetException
        super(Nuclide, self).__setattr__(key, value)

    def __iter__(self):
        for key in self.props:
            yield (key, getattr(self, key))
