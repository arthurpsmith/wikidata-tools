import csv

ror_md_file = 'ror_metadata.csv'
wd_ror_file = 'wikidata_ror.csv'

ror_names = {}
ror_wdids = {}
with open(ror_md_file) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        ror_id = row[0]
        name = row[1]
        wikidata_id = row[5]
        ror_names[ror_id] = name
        if wikidata_id is not None:
            if wikidata_id != '':
                ror_wdids[ror_id] = wikidata_id

wditems_ror = {}
wditems_by_ror = {}
with open(wd_ror_file) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        wikidata_id = row[0]
        ror_id = row[1]
        wditems_by_ror[ror_id] = wikidata_id
        if wikidata_id in wditems_ror:
            wditems_ror[wikidata_id].append(ror_id)
        else:
            wditems_ror[wikidata_id] = [ror_id]

with open('ror_wd_diffs.csv', 'w') as diffs_file:
    diffs_writer = csv.writer(diffs_file)
    diffs_writer.writerow(['Wikidata ID','ROR ID','WDID from ROR','Note'])
    for qid in wditems_ror.keys():
        id_list = wditems_ror[qid]
        for ror_id in id_list:
            if ror_id not in ror_names:
                diffs_writer.writerow([qid,ror_id,None,"not in ROR"])
            else:
                if ror_names[ror_id] == '':
                    diffs_writer.writerow([qid,ror_id,None,"blank name in ROR"])
            if ror_id in ror_wdids:
                if ror_wdids[ror_id] != qid:
                    diffs_writer.writerow([qid,ror_id,ror_wdids[ror_id],"differs in ROR"])
    for ror_id in ror_wdids:
        if ror_id not in wditems_by_ror:
            diffs_writer.writerow([None,ror_id,ror_wdids[ror_id],"missing in Wikidata"])
