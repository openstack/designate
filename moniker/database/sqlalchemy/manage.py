#!/usr/bin/env python
# this is a tempoary file - need to create a "moniker-manage" script as glance 
# and reddwarf have to run the migration using the main conf file for db creds
from migrate.versioning.shell import main

if __name__ == '__main__':
    main(url='sqlite:///test.sqlite', debug='True', repository='migrate_repo')
