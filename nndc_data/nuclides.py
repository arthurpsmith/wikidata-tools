#
# Stripped down from wikidata periodic table (chemistry.py originally)
#
import json
import operator
from units import time_quantity_in_seconds
from urllib import urlencode
from urllib2 import urlopen
from collections import defaultdict


def get_json(url, data):
    return json.load(urlopen(url, urlencode(data)))


class NuclideProvider(object):
    """Base class for nuclide providers."""

    WD_API = 'http://www.wikidata.org/w/api.php'
    API_LIMIT = 50
    WDQ_API = 'http://wdq.wmflabs.org/api'

    def __init__(self, language):
        self.language = language

    @classmethod
    def get_available_languages(cls):
        query = dict(action='query', format='json', meta='siteinfo', siprop='languages')
        result = get_json(cls.WD_API, query).get('query', {}).get('languages', [])
        return [lang['code'] for lang in result]

    @classmethod
    def get_entities(cls, ids, **kwargs):
        entities = {}
        query = dict(action='wbgetentities', format='json', **kwargs)
        for index in range(0, len(ids), cls.API_LIMIT):
            query['ids'] = '|'.join(ids[index:index + cls.API_LIMIT])
            new_entities = get_json(cls.WD_API, query).get('entities', {})
            entities.update(new_entities)
        return entities

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
        nuclides.sort(key=operator.attrgetter('atomic_number', 'neutron_number'))
        return nuclides


class WdqNuclideProvider(NuclideProvider):
    """Load nuclides from Wikidata Query."""
    def __iter__(self):
        wdq = self.get_wdq()
        ids = ['Q%d' % item_id for item_id in wdq['items']]
        entities = self.get_entities(ids, props='labels|claims',
                                     languages=self.language, languagefallback=1)
        nuclides = defaultdict(Nuclide)
        wdq['props'] = defaultdict(list, wdq.get('props', {}))
        for item_id, datatype, value in wdq['props'][str(Nuclide.atomic_number_pid)]:
            if datatype != 'quantity':
                continue
            value = value.split('|')
            if len(value) == 4:
                value = map(float, value)
                if len(set(value[:3])) == 1 and value[3] == 1 and value[0] == int(value[0]):
                    nuclides[item_id].atomic_number = int(value[0])
        for item_id, datatype, value in wdq['props'][str(Nuclide.neutron_number_pid)]:
            if datatype != 'quantity':
                continue
            value = value.split('|')
            if len(value) == 4:
                value = map(float, value)
                if len(set(value[:3])) == 1 and value[3] == 1 and value[0] == int(value[0]):
                    nuclides[item_id].neutron_number = int(value[0])
        for item_id, datatype, value in wdq['props'][str(Nuclide.decay_mode_pid)]:
            if datatype != 'item':
                continue
            nuclides[item_id].decay_modes.append(value)
        for item_id, nuclide in nuclides.items():
            nuclide.item_id = 'Q%d' % item_id
            for prop in ('atomic_number', 'neutron_number'):
                if not hasattr(nuclide, prop):
                    setattr(nuclide, prop, None)
# ??            nuclide.load_data_from_superclasses(subclass_of[item_id])
            label = None
            entity = entities.get(nuclide.item_id)
            if entity and 'labels' in entity and len(entity['labels']) == 1:
                label = entity['labels'].values()[0]['value']
            nuclide.label = label

            if entity:
              claims = entity['claims']
              instance_prop = 'P%d' % Nuclide.instance_pid
              if instance_prop in claims:
                instance_claims = claims[instance_prop]
                for instance_claim in instance_claims:
                  class_id = instance_claim['mainsnak']['datavalue']['value']['numeric-id']
                  if class_id == Nuclide.stable_qid:
                    nuclide.classes.append("stable")

	    half_life = None;
            if entity:
                claims = entity['claims']
		hlprop = 'P%d' % Nuclide.half_life_pid
                if hlprop in claims:
                  hl_claims = claims[hlprop]
                  for hl_claim in hl_claims:
		    half_life = time_quantity_in_seconds(hl_claim)
            nuclide.half_life = half_life
            yield nuclide 

    @classmethod
    def get_wdq(cls):
        pids = [str(getattr(Nuclide, name))
                for name in ('atomic_number_pid', 'neutron_number_pid', 'decay_mode_pid')]
        query = {
            'q': 'claim[%d:(tree[%d][][%d])] AND noclaim[%d:%d]' % (Nuclide.instance_pid, Nuclide.isotope_qid, Nuclide.subclass_pid, Nuclide.instance_pid, Nuclide.isomer_qid),
            'props': ','.join(pids)
        }
        return get_json(cls.WDQ_API, query)


class PropertyAlreadySetException(Exception):
    """Property already set."""


class Nuclide(object):

    props = ('atomic_number', 'neutron_number', 'item_id', 'label', 'half_life', 'decay_modes')
    atomic_number_pid = 1086
    neutron_number_pid = 1148
    half_life_pid = 2114
    decay_mode_pid = 817
    instance_pid = 31 
    subclass_pid = 279
    isotope_qid = 25276 # top-level class under which all isotopes to be found
    stable_qid = 878130 # id for stable isotope
    isomer_qid = 846110 # metastable isomers all instances of this

    def __init__(self, **kwargs):
	self.decay_modes = []
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

