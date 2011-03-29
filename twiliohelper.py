#!/usr/bin/python

import datetime
import jirahelpers
import logging
import twilio

module = 'twiliohelper'
logger = logging.getLogger(module)
API_VERSION = '2010-04-01'

def get_account(config):
    account = twilio.Account(config.twilio_account_sid, config.twilio_account_token)
    return account

def sms_issue(config, issue, recipient_list):
    """Helper method to send an sms of the issue defined by the bson dictionary issue"""
    logger.info('Send sms of %s' % (issue["_id"]))
    account = get_account(config)
    msg = get_sms_body(issue)
    receivers = recipient_list.split(',')
    logger.debug(receivers)
    for receiver in receivers:
        if len(receiver.strip()) > 0:
            logger.info('Sending SMS to %s' % (receiver))
            body = {
                    'From' : config.twilio_caller_id,
                    'To' : receiver,
                    'Body' : msg
                    }
            account.request('/%s/Accounts/%s/SMS/Messages' % (API_VERSION, config.twilio_account_sid), 'POST', body)
            logger.info('Sent SMS')

def get_sms_body(issue):
    """Helper method to create an sms body of the issue bson"""
    logger.info('Get sms body')
    mail_body = ['Id=']
    mail_body.append(issue["_id"])
    mail_body.append(' priority=')
    mail_body.append(str(issue["priority"]))
    mail_body.append(' company=')
    mail_body.append(issue.get('company', 'Unknown'))
    mail_body.append(' reporter=')
    mail_body.append(issue["reporter"])
    mail_body.append(' created=')
    mail_body.append(issue["jiraCreationTime"].strftime('%Y/%m/%d %H:%M:%S'))
    return ''.join(mail_body)

def escalate(config, recipient_list, subject, issues):
    logger.info('Escalate to phone')
    account = get_account(config)
    receivers = recipient_list.split(',')
    logger.debug(receivers)
    for receiver in receivers:
        if len(receiver.strip()) > 0:
            logger.info('Escalating to %s' % (receiver))
            body = {
                    'From' : config.twilio_caller_id,
                    'To' : receiver,
                    'Url' : config.twilio_callback_url
                    }
            account.request('/%s/Accounts/%s/Calls' % (API_VERSION, config.twilio_account_sid), 'POST', body)
    
if __name__ == '__main__':
    logfilename = module+'.log'
    logging.basicConfig(filename=logfilename, level=logging.DEBUG)
    config = jirahelpers.get_config()
    logger.debug(config.__dict__)
    issue = {
             '_id' : 'ID1',
             'priority' : 3,
             'company' : '10gen.com',
             'reporter' : 'sridhar',
             'jiraCreationTime' : datetime.datetime.now()
             }
    try:
        #sms_issue(config, issue)
        escalate()
    except Exception, e:
        print e;
        print e.read()
