#!/usr/bin/python

import confighelper
import datetime
import jirahelpers
import logging
import mongohelper

module = 'seedusers'
logger = logging.getLogger(module)

class User(object):
    def __init__(self, jiraid, firstname, lastname, email, cell):
        self.jiraid = jiraid
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.cell = cell

def main():
    logger.info('%s started' % (module))
    config = confighelper.get_config()
    logger.info('Obtained config')
    logger.debug(config.__dict__)
    mongohelper.initialize(config)
    logger.info('Mongo initialized')
    mongohelper.seed_users(config, get_users_from_file('userlist.txt'))
    
def get_users_from_file(filename):
    userlist = []
    with open(filename, 'r') as f:
        for line in f:
            user = line.split(',')
            firstname = user[0].strip()
            if (firstname == 'First Name'):
                continue
            logger.debug('Fields = %d user=%s' % (len(user), user))
            try:
                jiraid= user[9].strip()
            except:
                jiraid = None
            logger.debug('Jira id is %s' % (jiraid))
            if (jiraid is None or jiraid == ""):
                continue
            firstname = user[0].strip()
            lastname = user[1].strip()
            email = user[4].strip()
            cell = user[2].strip()
            logger.debug('User name=%s User id=%s User cell=%s'  % 
                         (jiraid, email, cell))
            user = User(jiraid, firstname, lastname, email, cell)
            userlist.append(user)
    return userlist 
    
if __name__ == '__main__':
    logfilename = module+'.log'
    logging.basicConfig(filename=logfilename, level=logging.ERROR)
    main()
    
    