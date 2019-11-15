#!/usr/bin/env python
import argparse
import time
import os
import shlex
import subprocess
import sys
import glob
import pip
import re
from os import path
from os.path import expanduser
import shutil


def pipe(args):
    """
    Call the process with std(in,out,err)
    """
    process = subprocess.Popen(
        args,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    process.wait()

    return process.returncode


def install_apt_packages():
    """
    Install debian dependencies.
    """
    package_list = set()

    for packages in glob.glob("/addons/**/apt-packages.txt"):
        print("Installing packages from %s" % packages)
        with open(packages, 'r') as pack_file:
            lines = [line.strip() for line in pack_file]
            package_list.update(set(lines))

    if len(package_list) > 0:
        ret = pipe(['apt-get', 'update'])

        # Something went wrong, stop the service as it's failing
        if ret != 0:
            sys.exit(ret)

        ret = pipe(['apt-get', 'install', '-y'] + list(package_list))

        # Something went wrong, stop the service as it's failing
        if ret != 0:
            sys.exit(ret)


def load_secrets():
    # TODO add a way to load some secrets so odoo process can
    # use secrets as a way to load passwords/user for postgresql
    # credentials could also be stored in the HOME of the odoo user
    # except we cannot rely on secrets 100% because it only works in
    # swarm mode
    pgpass_secret = '/run/secrets/.pgpass'
    if path.exists(pgpass_secret):
        home_folder = '/var/lib/odoo'
        pgpass_target = path.join(home_folder, '.pgpass')
        if path.exists(pgpass_target):
            os.remove(pgpass_target)
        # shutil.move doesn't always work correctly on different fs
        shutil.copy(pgpass_secret, home_folder)
        # Cannot remove anymore apparently
        # os.remove(pgpass_secret)
        # shutil.move(pgpass_secret, home_folder)


def fix_access_rights():
    pipe(["chown", "-R", "odoo:odoo", "/var/lib/odoo"])
    pipe(["chown", "-R", "odoo:odoo", "/etc/odoo"])


def remove_sudo():
    return pipe(["sed", "-i", "/odoo/d", "/etc/sudoers"])


def main():
    install_apt_packages()
    load_secrets()
    fix_access_rights()
    return remove_sudo()


try:
    code = main()
    sys.exit(code)
except Exception as exc:
    print(exc)
    sys.exit(1)
except KeyboardInterrupt as exc:
    print(exc)
    sys.exit(1)
