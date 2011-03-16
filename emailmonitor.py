#!/usr/bin/python
  
import datetime
import jirahelpers
import logging
import mailhelpers
import mongohelper
import pymongo
import sys
import time
import traceback

module = 'emailmonitor'
logger = logging.getLogger(module)
config = None

thirtyminutes = datetime.timedelta(minutes=30)
fortyminutes = datetime.timedelta(minutes=40)
fiftyminutes = datetime.timedelta(minutes=50)

def initialize():
    logger.info('In initialize')
    mongohelper.initialize(config.mongohost, 
                           config.mongoport, 
                           config.mongo_max_retry)
    logger.info('Mongo initialized')

def classify_issues(issues):
    thirtyminuteoldissues = []
    fortyminuteoldissues = []
    fiftyminuteoldissues = []
    currenttime = datetime.datetime.utcnow()
    for issue in issues:
        issue_creation_time = issue['jiraCreationTime']
        if issue_creation_time + fiftyminutes < currenttime:
            fiftyminuteoldissues.append(issue)
        elif issue_creation_time + fortyminutes < currenttime:
            fortyminuteoldissues.append(issue)
        elif issue_creation_time + thirtyminutes < currenttime:
            thirtyminuteoldissues.append(issue)
    
    logger.info('Got %d 50 mt old unassigned issues' % (len(fiftyminuteoldissues)))
    logger.info('Got %d 40 mt old unassigned issues' % (len(fortyminuteoldissues)))
    logger.info('Got %d 30 mt old unassigned issues' % (len(thirtyminuteoldissues)))
    return fiftyminuteoldissues, fortyminuteoldissues, thirtyminuteoldissues

def main(input_config):
    global config
    try:
        logger.info('Started %s monitor' % (module))
        config = input_config
        initialize()
        logger.info('Getting unassigned issues')
        issues = mongohelper.get_unassigned_issues(config.mongohost, 
                                                   config.mongoport, 
                                                   config.mongo_max_retry)
        logger.info('Got %d getting unassigned issues' % len(issues))                
        if len(issues) > 0:
            fiftyminuteoldissues, fortyminuteoldissues, thirtyminuteoldissues = classify_issues(issues)
            if len(fiftyminuteoldissues) > 0:
                logger.info('Emailing 50 minute old issues')
                mailhelpers.email_issues(config, 
                                         config.phone_escl_id, 
                                         'List of issues that are open for atleast 50', 
                                         fiftyminuteoldissues)
                logger.info('Done emailing 50 minutes issues')
            if len(fortyminuteoldissues) > 0:
                logger.info('Emailing 40 minute old issues')
                mailhelpers.email_issues(config, 
                                         config.dev_id, 
                                         'List of issues that are open for atleast 40 minutes but less than 50', 
                                         fortyminuteoldissues)
                logger.info('Done emailing 40 minutes issues')
            if len(thirtyminuteoldissues) > 0:
                logger.info('Emailing 30 minute old issues')
                mailhelpers.email_issues(config, 
                                         config.support_id, 
                                         'List of issues that are open for atleast 30 minutes but less than 40', 
                                         thirtyminuteoldissues)
                logger.info('Done emailing 30 minutes issues')
    except:
        error = traceback.format_exc()
        logger.critical(error)
        mailhelpers.alert_admin(config, 
                                module,
                                error)
        raise

if __name__ == '__main__':
    logfilename = module + '.log'
    logging.basicConfig(filename=logfilename, level=logging.DEBUG)
    config = jirahelpers.get_config()
    main(config)
