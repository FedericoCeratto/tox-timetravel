#!/usr/bin/env python

from argparse import ArgumentParser
import configparser
import json
import re
import urllib2

PYPI_URL = "https://pypi.python.org/pypi/%s/json"
PKG_NAME_PATTERN = re.compile('[a-zA-Z0-9\.-]*')


def parse_tox_ini(fname, snapshot_date, list_all):
    """Parse tox.ini file and perform version selection for every testenv
    """
    cp = configparser.SafeConfigParser()
    cp.read(fname)
    for sn in cp.sections():
        if not sn.startswith('testenv'):
            continue
        if not cp.has_option(sn, 'deps'):
            continue

        deps = []
        for dep in cp.get(sn, 'deps').splitlines():
            if dep.split(' ')[0].endswith(':'):
                # remove Tox label
                dep = dep.split(' ')[1]
                deps.append(dep)
            else:
                deps.append(dep)

        print("[%s]" % sn)
        package_names = parse_requirements(deps)
        for pn in package_names:
            fetch_versions(pn, snapshot_date, list_all)


def parse_requirements(lines):
    """Parse requirements list, ignore comments and version filters
    """
    package_names = []
    for line in lines:
        line = line.strip()
        if line.startswith(('-', '#')):
            continue

        pn = PKG_NAME_PATTERN.match(line).group()
        if pn:
            package_names.append(pn)

    return package_names


def calc_snapshot_date(d):
    """Calculate snapshot date, fill missing month/day
    """
    d = d.replace('-', '')
    if len(d) == 4:
        return d + '0101'
    if len(d) == 6:
        return d + '01'
    if len(d) == 8:
        return d

    raise RuntimeError("Date must be YYYY or YYYY-MM or YYYY-MM-DD")


def fetch_versions(pn, snapshot_date, list_all):
    """Fetch versions from PyPI and print selected release
    """
    try:
        data = urllib2.urlopen(PYPI_URL % pn)
    except urllib2.HTTPError as e:
        print "Unable to fetch", PYPI_URL % pn
        return

    data = json.load(data)

    releases = [
        (min(chunk['upload_time'] for chunk in release_data), version)
        for version, release_data in data['releases'].iteritems()
        if release_data
    ]
    releases = sorted(releases, reverse=True)
    found = False
    for rdate, version in releases:
        if rdate > snapshot_date:
            if list_all:
                print("%-20s %20s %s" % (pn, version, rdate))
            continue

        if list_all:
            if found:
                print("%-20s %20s %s" % (pn, version, rdate))
            else:
                print("%-20s %20s %s *" % (pn, version, rdate))
                found = True
        else:
            print pn, version
            return

    if not found:
        print pn, 'no candidate version found'


def main():
    ap = ArgumentParser()
    ap.add_argument('-d', '--debug', action='store_true')
    ap.add_argument('-a', '--list-all', action='store_true',
                    help='list all releases')
    ap.add_argument('fname')
    ap.add_argument(
        'date',
        help="Snapshot date: YYYY YYYYMM YYYYMMDD YYYY-MM YYYY-MM-DD"
    )
    args = ap.parse_args()

    snapshot_date = calc_snapshot_date(args.date)

    if args.fname.endswith('requirements.txt'):
        with open(args.fname) as f:
            package_names = parse_requirements(f.readlines())

        for pn in package_names:
            fetch_versions(pn, snapshot_date, args.list_all)

    elif args.fname.endswith('tox.ini'):
        parse_tox_ini(args.fname, snapshot_date, args.list_all)


if __name__ == '__main__':
    main()
