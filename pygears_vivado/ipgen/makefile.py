import os
import jinja2
from pygears.util import py_files_enum
from pygears.util.fileio import save_if_changed


def makefile(top, design, outdir, include=None, **kwds):
    if include is None:
        include = []

    seen = set()
    seen_add = seen.add
    py_files = [x for x in py_files_enum(top) if not (x in seen or seen_add(x))]

    kwds['outdir'] = outdir
    kwds['top'] = top
    del kwds['build']
    del kwds['generate']

    kwds_s = []
    for name, val in kwds.items():
        if val is None:
            continue

        if isinstance(val, bool):
            if val:
                kwds_s.append(f'--{name}')

            continue

        val = str(val)

        if ' ' in val:
            val = f"'{val}'"

        kwds_s.append(f'--{name} {val}')

    context = {
        'py_sources': sorted(py_files),
        'kwds': kwds_s,
        'hdl_include_path': [f'-I {p}' for p in include],
        'design_path': design,
    }

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        trim_blocks=True,
        lstrip_blocks=True)
    env.globals.update(zip=zip)

    res = env.get_template('makefile.j2').render(context)

    save_if_changed('Makefile', outdir, res)
