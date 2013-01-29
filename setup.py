from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='il.spdo',
      version=version,
      description="SPDO",
      long_description=open("README.md").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Fabiano Weimar dos Santos',
      author_email='xiru@xiru.org',
      url='http://repositorio.interlegis.gov.br/il.spdo/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['il'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'five.grok',
          'plone.app.z3cform',
          'reportlab',
          'z3c.saconfig',
          'MySQL-python',
          'collective.saconnect',
          'plone.directives.form',
          'plone.formwidget.multifile',
          'plone.app.drafts',
          'plone.formwidget.autocomplete',
          'collective.z3cform.datetimewidget',
          'py-bcrypt',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      setup_requires=[],
      )
