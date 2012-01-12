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
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Plugins",
          "Framework :: Tryton",
          "Intended Audience :: Developers",
          "Intended Audience :: Financial and Insurance Industry",
          "Intended Audience :: Legal Industry",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Natural Language :: Bulgarian",
          "Natural Language :: Czech",
          "Natural Language :: Dutch",
          "Natural Language :: English",
          "Natural Language :: French",
          "Natural Language :: German",
          "Natural Language :: Russian",
          "Natural Language :: Spanish",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Topic :: Office/Business",
      ],
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['trytond','trytond.modules'],
      include_package_data=True,
      keywords='',
      license='',
      zip_safe=False,
      install_requires=requires,
      entry_points="""
      [trytond.modules]
      contract = trytond.modules.contract
      """,
      )
