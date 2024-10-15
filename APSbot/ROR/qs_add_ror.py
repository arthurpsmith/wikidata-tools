import csv

# Property values from live wikidata:
p_ror_id = 'P6782'
p_stated_in = 'S248'

ror_release_qid = 'Q130536621' # ROR release 1.53

def process_ror_data(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
#            junk, ror_id, org_qid, note = row
            ror_id, org_qid = row
            if org_qid is None:
                continue
            print('{0}	{1}	"{2}"	{3}	{4}'.format(
              org_qid, p_ror_id, ror_id, p_stated_in, ror_release_qid))


process_ror_data('ror_wikidata.csv')
