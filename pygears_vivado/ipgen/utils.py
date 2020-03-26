import os
import shutil


def get_folder_struct(outdir):
    dirs = {n: os.path.join(outdir, n) for n in ['hdl', 'script', 'driver']}
    dirs['root'] = outdir

    return dirs


def create_folder_struct(dirs):
    for k, d in dirs.items():
        os.makedirs(d, exist_ok=True)


def purge_folder_struct(dirs):
    for k, d in dirs.items():
        if k != 'root':
            shutil.rmtree(d, ignore_errors=True)

        os.makedirs(d, exist_ok=True)
