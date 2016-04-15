#!/usr/bin/env python3

from distutils.core import setup

setup(name='budgetless',
      version='0.1',
      description='A library and application for simple budget(less) analysis of finances.',
      author='Matthew Wardrop',
      author_email='mister.wardrop@gmail.com',
      url='http://www.matthewwardrop.info/',
      #download_url='https://github.com/matthewwardrop/python-relentless',
      packages=['budgetless','budgetless.providers','budgetless.ui'],
      package_data = {
              'budgetless.ui': ['templates/*.html', 'templates/panel/*.html', 'static/*.css', 'static/*.js']
          },
      requires=['parampy','pandas','numpy', 'sqlalchemy', 'plotly', 'matplotlib'],
      scripts=['scripts/budgetless']

     )
