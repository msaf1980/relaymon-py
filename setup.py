#!/usr/bin/python

import re
import os
import sys
import glob
import shlex
import subprocess
from setuptools import setup
from distutils.cmd import Command
from distutils.command.clean import clean
from distutils.errors import *

name = 'relaymon'
pname = 'relaymonitor'
testdir = 'tests'

release = False

def pkg_version(name):
    with open('%s/version.py' % name, 'r') as f:
        for line in f:
            m = re.match(r'^version * = *\"(.*)\"', line)
            if not m is None:
                v = m.group(1)
                m = re.match(r'^\"?([0-9]+)\.([0-9]+)\.([0-9]+)\"?$', v)
                if m is None:
                    raise ValueError("incorrect version: %s" % v)
                return "%d.%d.%d" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    raise ValueError("version not found")


class TestError(DistutilsError):
    pass


class RunTests(Command):
    user_options = []

    def initialize_options(self):
        self.xml_output = None

    def finalize_options(self): pass

    def run(self):
        os.chdir(testdir)
        pythonpath = os.environ.get('PYTHONPATH')
        if pythonpath is None:
            pythonpath = '..'
        else:
            pythonpath = '..:%s' % pythonpath
        os.environ['PYTHONPATH'] = pythonpath

        errors = 0
        for test in glob.glob('test_*.py'):
            base, ext = os.path.splitext(test)
            print(testdir + '/' + base)
            proc = subprocess.Popen([sys.executable, '-m', 'unittest', base])
            proc.communicate()
            rc = proc.returncode
            if rc != 0:
                errors += 1

        if errors > 0:
            raise TestError("test failed (%d)!" % errors)


class RunClean(clean):
    def run(self):
        global pname
        from os import path
        from os import remove
        import glob
        import shutil
        c = clean(self.distribution)
        c.all = True
        c.finalize_options()
        c.run()
        cdir = path.dirname(path.realpath(__file__))
        for f in glob.glob(path.join(cdir, pname, "*.pyc")):
            remove(f)
        try:
            remove(path.join(cdir, "MANIFEST"))
        except:
            pass
        shutil.rmtree(path.join(cdir, 'build'), ignore_errors=True)
        shutil.rmtree(path.join(cdir, 'dist'), ignore_errors=True)
        shutil.rmtree(path.join(cdir, name + '.egg-info'), ignore_errors=True)
        shutil.rmtree(path.join(cdir, pname, '__pycache__'), ignore_errors=True)
        shutil.rmtree(path.join(cdir, testdir, '__pycache__'), ignore_errors=True)

if __name__ == '__main__':
    release = os.environ.get('RELEASE', '0')
    if release == "1":
        GIT_HEAD_REV = ""
    else:
        GIT_HEAD_REV = subprocess.check_output(shlex.split('git rev-parse --short HEAD')).strip()

    if GIT_HEAD_REV == "":
        tag = ""
    else:
        tag="-dev_" + GIT_HEAD_REV

    setup(
        name=name,
        packages=[pname],
        scripts=[name],
        version=pkg_version(pname),
        description='graphite relay monitoring',
        url='http://github.com/msaf1980/relaymon',
        author='Michail Safronov',
        author_email='msaf1980@gmail.com',
        license='MIT',
        options=dict(egg_info=dict(tag_build=tag)),
        cmdclass={
            'test': RunTests,
            'clean': RunClean,
        },
    )
