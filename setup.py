from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))


def readme():
    with open(os.path.join(this_directory, 'README.rst'),
              encoding='utf-8') as f:
        return f.read()


setup(
    name='pygears-vivado',
    version='0.0.1',
    description='PyGears library for interfacing Vivado Xilinx tool',
    long_description=readme(),
    url='https://www.pygears.org',
    # download_url = '',
    author='Bogdan Vukobratovic',
    author_email='bogdan.vukobratovic@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    python_requires='>=3.6.0',
    install_requires=['pygears'],
    setup_requires=['pygears'],
    package_data={
        '': ['*.j2', '*.sv', '*.c', '*.h'],
        'drivers': ['*']
    },
    include_package_data=True,
    keywords=
    'Vivado PyGears functional hardware design Python simulator HDL ASIC FPGA',
    packages=find_packages(exclude=['docs']),
)
