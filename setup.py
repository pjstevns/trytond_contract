from setuptools import setup, find_packages
import re

info = eval(open('trytond/modules/contract/__tryton__.py').read())
major_version, minor_version, _ = info.get('version', '0.0.1').split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)

requires = []                                                                                                                                                          
for dep in info.get('depends', []):
    if not re.match(r'(ir|res|workflow|webdav)(\W|$)', dep):
        requires.append('trytond_%s >= %s.%s, < %s.%s' %
                        (dep, major_version, minor_version, major_version,
                         minor_version + 1))
requires.append('trytond >= %s.%s, < %s.%s' %
                (major_version, minor_version,
                 major_version, minor_version + 1))

setup(name='trytond_contract',
      version=info.get('version','0.0.1'),
      description=info.get('description',''),
      author=info.get('author',''),
      author_email=info.get('email',''),
      url=info.get('website',''),
      long_description=open('README.txt').read(),
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      packages=find_packages(exclude=['ez_setup']),
      package_data={
          'trytond.modules.contract': info.get('xml', []) \
          + info.get('translation', []),
      }, 
      keywords='',
      license='',
      zip_safe=False,
      install_requires=requires,
      entry_points="""
      [trytond.modules]
      contract = trytond.modules.contract
      """,
      )
