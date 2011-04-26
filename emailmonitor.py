#!/usr/bin/python

import confighelper  
import datetime
import jirahelpers
import logging
import mailhelpers
import mongohelper
import os
import pymongo
import sys
import time
import traceback
import twiliohelper

"""
All issues are no activity
Thresholds:
  Threshold 1 - blocker, 30 minutes old, whine email
  Threshold 2 - critical, 50 minutes old - whine email
  Threshold 3 - major, 2 hours old, whine email
  Threshold 4 - everything else, 4 hours old, whine email
"""

module = 'emailmonitor'
logger = logging.getLogger(module)
config = None

thirtyminutes = datetime.timedelta(minutes=30)
fiftyminutes = datetime.timedelta(minutes=50)
twohours = datetime.timedelta(hours=2)
fourhours = datetime.timedelta(hours=4)

def initialize():
    logger.info('In initialize')
    mongohelper.initialize(config)
    logger.info('Mongo initialized')

def classify_issues(issues):
    global category1issues, category2issues, category3issues, category4issues
    category1issues = []
    category2issues = []
    category3issues = []
    category4issues = []
    currenttime = datetime.datetime.utcnow()
    for issue in issues:
        issue_creation_time = issue['jiraCreationTime']
        issue_priority = issue['priority']
        if issue_priority == 1:
            """Blocker issue"""
            if issue_creation_time + thirtyminutes < currenttime:
                category1issues.append(issue)
        elif issue_priority == 2:
            """Critical issue"""
            if issue_creation_time + fiftyminutes < currenttime:
                category2issues.append(issue)
        elif issue_priority == 3:
            """Major issue"""
            if issue_creation_time + twohours < currenttime:
                category3issues.append(issue)
        else:
            if issue_creation_time + fourhours < currenttime:
                category4issues.append(issue)

def main(input_config):
    global config
    try:
        logger.info('Started %s monitor' % (module))
        config = input_config
        initialize()
        logger.info('Getting unattended issues')
        issues = mongohelper.get_unassigned_issues(config)
        logger.info('Got %d unattended issues' % len(issues))                
        if len(issues) > 0:
            classify_issues(issues)
            if len(category1issues) > 0:
                logger.info('Escalating category 1 issues')
                mailhelpers.email_issues(config, 
                                         config.dev_id, 
                                         'Blocker issues that are open for at least 30 minutes', 
                                         category1issues)
                logger.info('Done escalating category 1 issues')
            if len(category2issues) > 0:
                logger.info('Escalating category 2 issues')
                mailhelpers.email_issues(config, 
                                         config.dev_id, 
                                         'Critical issues that are open for at least 40 minutes', 
                                         category2issues)
                logger.info('Done escalating category 2 issues')
            if len(category3issues) > 0:
                logger.info('Escalating category 3 issues')
                mailhelpers.email_issues(config, 
                                         config.dev_id, 
                                         'Major issues that are open for at least 2 hours', 
                                         category3issues)
                logger.info('Done escalating category 3 issues')
            if len(category4issues) > 0:
                logger.info('Escalating category 4 issues')
                mailhelpers.email_issues(config, 
                                         config.dev_id, 
                                         'Issues that are open for at least 4 hours', 
                                         category4issues)
                logger.info('Done escalating category 4 issues')
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
    config = confighelper.get_config()
    main(config)
