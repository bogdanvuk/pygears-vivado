from itertools import islice

def row_data(line):
    return [row.strip().lower() for row in line.split('|') if row.strip()]


def parse_utilization(fn):
    with open(fn) as f:
        tbl_section = 0
        for line in f:
            if line[0] == '+':
                tbl_section += 1
            elif tbl_section == 1:
                header = row_data(line)[2:]
            elif tbl_section == 2:
                values = [float(v) for v in row_data(line)[2:]]
                break

        return dict(zip(header, values))


def parse_timing(fn):
    with open(fn) as f:
        line = next(islice(f, 2, None))
        elems = line.split()
        if len(elems) > 1:
            return float(line.split()[1])
