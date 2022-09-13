import csv

mismatches_file = 'mismatches_v1.0'
wd_redir_file = 'wikidata_redirects.csv'

wd_redirects = {}
with open(wd_redir_file) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        old_wd_id = row[0]
        new_wd_id = row[1]
        wd_redirects[old_wd_id] = new_wd_id

with open('correct_redirects.csv', 'w') as redir_correct_file:
    redir_writer = csv.writer(redir_correct_file)
    redir_writer.writerow(['ROR ID','Original Wikidata ID','Redirect Wikidata ID'])
    with open(mismatches_file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            wikidata_id = row[0]
            ror_id = row[1]
            ror_wd_id = row[2]
            if ror_wd_id in wd_redirects:
                wd_redir_id = wd_redirects[ror_wd_id]
                if wd_redir_id == wikidata_id:
                    redir_writer.writerow([ror_id, ror_wd_id, wikidata_id])
                else:
                    print("WARNING: redir still mismatched for {0}: {1} vs {2}".format(ror_id, wikidata_id, wd_redir_id))
