# nndc_data

Basic functionality here:
1. get list of nuclides in wikidata
2. check NNDC nudat2 page for data on each nuclide
3. Write out resulting information to a csv file

Tested with python 2.7

To fetch half-life data:
1. pip install -r requirements.txt
2. python get_nndc_half_lives.py > half_life_data.csv
