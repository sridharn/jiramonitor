#!/usr/bin/python
  
import jirahelpers
import logging
import mailhelpers
import mongohelper
import pymongo
import sys
import time
import traceback
import xmlrpclib

module = 'jiramonitor'
logger = logging.getLogger(module)
config = None
     
def process_filter(filter_id, auth, proxy):
    issues = jirahelpers.get_issues_by_filterid(auth, proxy, filter_id) 
    no_of_issues = len(issues) 
    if no_of_issues < 1:
        return
    logger.info('Number of issues obtained from JIRA %d' % (no_of_issues))
    mongohelper.store_issues_to_mongo(config.mongohost, 
                                      config.mongoport, 
                                      config.mongo_max_retry,
                                      issues)

def update_issues(auth, proxy):
    issues = mongohelper.get_unassigned_issues(config.mongohost, 
                                               config.mongoport, 
                                               config.mongo_max_retry)
    valid_commenters = mongohelper.get_commenters(config.mongohost, 
                                                  config.mongoport, 
                                                  config.mongo_max_retry)
    for issue in issues:
        issueid = issue['_id']
        commenters = jirahelpers.get_issue_commenters(auth, proxy, issueid)
        valid_comments = valid_commenters & commenters
        if len(valid_comments) > 0:
            mongohelper.set_inprogress(config.mongohost, 
                                       config.mongoport, 
                                       config.mongo_max_retry,
                                       issueid)
    
    
def initialize():
    global sender, admin_email, admin_sms, smtp_password
    logger.info('In initialize')
    mongohelper.initialize_and_seed(config.mongohost, 
                                    config.mongoport, 
                                    config.mongo_max_retry)
    logger.info('Mongo initialized')
    proxy, auth = jirahelpers.auth_against_jira(config.jirauri, 
                                                config.jirauser, 
                                                config.jirapassword, 
                                                config.jira_max_errors)
    logger.info('Authenticated against JIRA')
    return proxy, auth

def main(input_config):
    global config
    try:
        logger.info('Started %s monitor' % (module))
        config = input_config
        proxy, auth = initialize()
        process_filter(config.filter_id, auth, proxy)
        logger.info('Filter processed')
        update_issues(auth, proxy)
        logger.info('Updated issues')
    except:
        error = traceback.format_exc()
        logger.critical(error)
        mailhelpers.alert_admin(config,
                                module,
                                error)
        raise
    
if __name__ == '__main__':
    logfilename = module+'.log'
    logging.basicConfig(filename=logfilename, level=logging.DEBUG)
    config = jirahelpers.get_config()
    main(config)
