# time units and their values in multiples of seconds
time_units = {
    11574: 1.0,          # second
    7727: 60.0,          # minute
    25235: 3600.0,       # hour
    573: 86400.0,        # day
    23387: 604800.0,     # week
    5151: 2.630e6,       # month (average)
    1092296: 3.156e7,    # year (annum)
    577: 3.156e7,        # year (calendar)
    723733: 1.0e-3,      # millisecond
    842015: 1.0e-6,      # microsecond
    838801: 1.0e-9,      # nanosecond
    3902709: 1.0e-12,    # picosecond
    1777507: 1.0e-15,    # femtosecond
    2483628: 1.0e-18     # attosecond
}


def time_in_seconds_from_claim(claim):
    amount = None
    if 'mainsnak' in claim:
        if 'datavalue' in claim['mainsnak']:
            quantity = claim['mainsnak']['datavalue']['value']
            amount = time_in_seconds(quantity['amount'], quantity['unit'])
    return amount


def time_in_seconds(amount_str, unit_uri):
    amount = float(amount_str)
    unit_id = int(unit_uri.split('/')[-1].replace('Q', ''))
    amount *= time_units[unit_id]
    return amount
