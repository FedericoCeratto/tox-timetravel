# tox-timetravel
A simple tool to select package releases from PyPI by date.
Useful to create Tox configurations to test your project against older libraries in a consistent manner.

It can extract versions from tox.ini and requirements.txt

Example: show dependencies version on 2014-01-01
```
  ./timetravel.py tox.ini 2014   
  [testenv]
  beaker 1.6.4
  bottle 0.12.8
  scrypt 0.6.1
  sqlalchemy 0.9.8
  webtest 2.0.17
```
