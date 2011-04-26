#!/usr/bin/python

import confighelper
import jirahelpers
import logging
import mailhelpers
import twiliohelper
import mongohelper
import os
import pymongo
import sys
import time
import traceback
 
module = 'smsmonitor'
logger = logging.getLogger(module)
config = None
sms_numbers = []

def initialize():
    global sender, admin_email, admin_sms, smtp_password
    logger.info('In initialize')
    mongohelper.initialize(config)
    logger.info('Mongo initialized')
    
def sms_issue(config, issue):
    if os.environ.get('USETWILIOSMS'):
        logger.debug('Using twilio')
        twiliohelper.sms_issue(config, issue, get_sms_phones())
    else:
        logger.debug('Using mail')
        mailhelpers.sms_issue(config, issue, get_sms_emails())

def get_sms_emails():
    return config.sms_id

def get_sms_phones():
    return config.twilio_sms_notifs
    
def main(input_config):
    global config, sms_numbers
    try:
        logger.info('Started %s monitor' % (module))
        config = input_config
        initialize()
        error_count = 0
        sms_numbers= mongohelper.get_oncall_sms_nos(config)
        logger.debug(sms_numbers)
        while error_count <= config.email_max_errors:
            try:
                issue = mongohelper.get_new_issue(config)
                if issue != None:
                    logger.debug('Got issue %s' % (issue.__str__()))
                    sms_issue(config, issue)
                else:
                    logger.info('No issues to notify')
                    break
            except pymongo.errors.AutoReconnect as pmar:
                logger.error(pmar)
                error_count += 1
                mongohelper.initialize(config)
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
    logging.basicConfig(filename=logfilename, level=logging.DEBUG)
    config = confighelper.get_config()
    main(config)
