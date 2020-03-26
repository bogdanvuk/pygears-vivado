import shutil
import jinja2
import os
from pygears import registry
from pygears.hdl import hdlgen, list_hdl_files
from pygears.hdl.yosys import synth as yosys_synth


def generate(
    top,
    outdir,
    lang,
    util,
    timing,
    prjdir,
    yosys_preproc=True):

    if lang not in ['sv', 'v']:
        raise Exception(f"Synth test unknown language: {lang}")

    hdlgen(top=top, language=lang, outdir=outdir, wrapper=(lang == 'sv'))

    vgen_map = registry(f'{lang}gen/map')
    top_name = vgen_map[top].module_name

    if lang == 'sv' or not yosys_preproc or not shutil.which('yosys'):
        files = list_hdl_files(top, outdir, lang, wrapper=True)
        top_name = f'wrap_{top_name}'
    else:
        files = [os.path.join(outdir, 'synth.v')]
        files.append(os.path.join(os.path.dirname(__file__), 'yosys_blocks.v'))

        yosys_synth(
            outdir=outdir,
            srcdir=outdir,
            rtl_node=top,
            synth_out=files[0],
            synth_cmd='synth -noalumacc -noabc -run coarse')

    jinja_context = {
        'res_dir': prjdir,
        'files': files,
        'top': top_name,
        'util': util,
        'timing': timing
    }

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=os.path.dirname(__file__)))

    env.get_template('synth.j2').stream(jinja_context).dump(f'{outdir}/synth.tcl')

