# -*- coding: utf-8 -*-
"""
Created on Thu Aug 16 20:54:36 2018
"""

from setuptools import setup, find_packages
#from textwrap import dedent
#import os
#
#NAME = 'mountaineer_bot'
#AUTHOR = 'Three Mountaineers'
#
#MAJOR = 1
#MINOR = 0
#MICRO = 0
#DEVVAR = '0'
#ISRELEASED = True
#DESCRIPTION = ("Bot for three_mountaineers")
#
#def write_version_py(filename=r'mountaineer_bot/version.py'):
#
#    cnt = """
#    # THIS FILE IS GENERATED FROM SCIPY SETUP.PY
#    short_version = '{version}'
#    version = '{version}'
#    release = {isrelease}
#    """
#    cnt = dedent(cnt)
#    if ISRELEASED:
#        VERSION = '%d.%d.%d' % (MAJOR, MINOR, MICRO)
#    else:
#        VERSION = '%d.%d.%d.dev%s' % (MAJOR, MINOR, MICRO, DEVVAR)
#
#    path = os.path.abspath(os.path.dirname(__file__))
#    with open(os.path.join(path,filename), 'w+') as a:
#        a.write(cnt.format(**{'version': VERSION,
#                       'isrelease': str(ISRELEASED)}))
#    return VERSION
#
#VERSION = write_version_py()
#
#setuptools_kwargs = {
#    'name': NAME,
#    'version': VERSION,
#    'author': AUTHOR,
#    'description': DESCRIPTION,
#    'packages':find_packages(exclude=['tests.*','tests*']),
#    'include_package_data':True,
#    'install_requires': [
#        'twitchio>=2.6.0',
#        'twitchAPI>=3.10.0',
#        'keyring>=23.13.1',
#        'requests>=2.30.0',
#        'flask>=2.3.2',
#        'pytz>=2023.3',
#        'tzlocal>=5.2',
#        'appdirs>=1.4.4',
#    ],
#    'zip_safe': False
#}
#
#setup(**setuptools_kwargs)
setup()