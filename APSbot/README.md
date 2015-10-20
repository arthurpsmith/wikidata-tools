# APSbot
Bot account to query and update wikidata...

Tested with python 3.4

The bot code runs in a cloned copy of pywikibot:

git clone --recursive https://gerrit.wikimedia.org/r/pywikibot/core.git

See https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
for details.

# APSbot_nuclides.py
Update wikidata with nuclide information from NNDC (via a CSV file).

To run this (after setting up the bot account etc...)

1. Copy the half-life data csv file (from nndc_data/get_nndc_half_lives.py) - currently this code uses a specific filename in the local directory ('test.csv')

2. python pwb.py APSbot_nuclides.py


