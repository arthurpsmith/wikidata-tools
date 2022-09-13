import csv

ror_md_file = 'ror_metadata.csv'
wd_ror_file = 'wikidata_ror.csv'

wditems_by_ror = {}
with open(wd_ror_file) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        wikidata_id = row[0]
        ror_id = row[1]
        wditems_by_ror[ror_id] = wikidata_id

with open('ror_or_metadata.csv', 'w') as or_file:
    or_writer = csv.writer(or_file)
    with open(ror_md_file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            ror_id = row[0]
            if ror_id == 'ROR ID':
                row[6:6] = ['Reverse Wikidata ID']
            else:
                if ror_id in wditems_by_ror:
                    row[6:6] = [wditems_by_ror[ror_id]]
                else:
                    row[6:6] = [None]
            or_writer.writerow(row)
