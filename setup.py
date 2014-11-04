from setuptools import setup, find_packages
import simso

setup(
    name='SimSo',
    version=simso.__version__,
    description='Simulation of Multiprocessor Real-Time Scheduling with Overheads',
    author='Maxime Cheramy',
    author_email='maxime.cheramy@laas.fr',
    url='http://homepages.laas.fr/mcheramy/simso/',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    packages=find_packages(),
    install_requires=[
        'SimPy==2.3.1',
        'numpy>=1.6'
    ],
    entry_points={
        'gui_scripts': ['simso = simso:run_gui']
    },
)
