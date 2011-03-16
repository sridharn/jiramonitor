#!/usr/bin/python

import jirahelpers
import logging
import mailhelpers
import mongohelper
import pymongo
import sys
import time
import traceback
 
module = 'smsmonitor'
logger = logging.getLogger(module)
config = None

def initialize():
    global sender, admin_email, admin_sms, smtp_password
    logger.info('In initialize')
    mongohelper.initialize(config.mongohost, 
                           config.mongoport, 
                           config.mongo_max_retry)
    logger.info('Mongo initialized')
    
def main(input_config):
    global config
    try:
        logger.info('Started %s monitor' % (module))
        config = input_config
        initialize()
        error_count = 0
        while error_count <= config.email_max_errors:
            try:
                issue = mongohelper.get_new_issue(config.mongohost, 
                                                  config.mongoport,
                                                  config.mongo_max_retry)
                if issue != None:
                    logger.debug('Got issue %s' % (issue.__str__()))
                    mailhelpers.sms_issue(config, 
                                          issue)
                else:
                    logger.info('No issues to notify')
                    break
            except pymongo.errors.AutoReconnect as pmar:
                logger.error(pmar)
                error_count += 1
                mongohelper.initialize(config.mongohost, 
                                       config.mongoport,
                                       config.mongo_max_retry)
            except mongohelper.CannotConnectToMongo as cctm:
                logger.critical('Cannot connect to Mongo %s' % (cctm))
                raise
            except:
                logger.error(traceback.format_exc())
                error_count += 1
    except:
        error = traceback.format_exc()
        logger.critical(error)
        mailhelpers.alert_admin(config, 
                                module, 
                                error)
        raise

if __name__ == '__main__':
    logfilename = module+'.log'
    logging.basicConfig(filename=logfilename, level=logging.ERROR)
    config = jirahelpers.get_config()
    main(config)
