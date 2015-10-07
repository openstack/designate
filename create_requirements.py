#!/usr/bin/python
from __future__ import print_function

import os

def file_requirement(root, req):
    _, _, path = req.partition(':')
    return os.path.normpath(os.path.join(root, path))


def main():
    here = os.getcwd()
    os.rename('requirements.txt', 'requirements-py2.txt')

    requirements = []
    with open('rackspace-requirements.txt') as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('file:'):
                requirements.append(file_requirement(here, line))
            else:
                requirements.append(line)

    with open('requirements.txt', 'w+') as reqs:
        reqs.write('\n'.join(requirements))

    print('Requirements.txt:')
    print(open('requirements.txt').read())


if __name__ == '__main__':
    main()
