import shutil
import jinja2
import os
from pygears import reg
from pygears.hdl import hdlgen, list_hdl_files
from pygears.hdl.yosys import synth as yosys_synth
from pygears.util.fileio import save_file


def generate(top, outdir, lang, util, timing, prjdir, part,
             yosys_preproc=True):

    if lang not in ['sv', 'v']:
        raise Exception(f"Synth test unknown language: {lang}")

    if lang == 'sv':
        yosys_preproc = False

    hdlgen(top=top, lang=lang, toplang=lang, outdir=outdir)

    vgen_map = reg['hdlgen/map']
    top_name = vgen_map[top].wrap_module_name

    if not yosys_preproc or not shutil.which('yosys'):
        files = list_hdl_files(top, outdir, lang, wrapper=True)

        if lang == 'sv':
            save_file(f'{top_name}_synth_wrap.sv', outdir,
                      vgen_map[top].get_synth_wrap(reg[f'svgen/templenv']))
            top_name = f'{top_name}_synth_wrap'
            files.append(os.path.join(outdir, f'{top_name}.sv'))
    else:
        files = [os.path.join(outdir, 'synth.v')]
        # files.append(os.path.join(os.path.dirname(__file__), 'yosys_blocks.v'))

        yosys_synth(outdir=outdir,
                    srcdir=outdir,
                    top=top,
                    synthout=files[0],
                    synthcmd='synth -noalumacc -noabc -run coarse')

    jinja_context = {
        'res_dir': prjdir,
        'files': files,
        'top': top_name,
        'util': util,
        'timing': timing,
        'part': part
    }

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(
        searchpath=os.path.dirname(__file__)))

    env.get_template('synth.j2').stream(jinja_context).dump(
        f'{outdir}/synth.tcl')
