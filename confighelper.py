#!/usr/bin/python

import ConfigParser
import logging

module = 'confighelper'
logger = logging.getLogger(module)

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

class Config(object):
    """Class to hold config values read from OS config file"""
    def __init__(self):
        mongohost = 'localhost'
        mongoport = 27017
        
def get_config():
    """Helper method to read from config values from file jiramonitor.cfg. This should be local to the script"""
    config_parser = ConfigParser.RawConfigParser()
    config_parser.read('jiramonitor.cfg')
    
    config = Config() 
    
    config.jirauser = config_parser.get('Jira', 'user')
    config.jirapassword = config_parser.get('Jira', 'password')
    config.jirauri = config_parser.get('Jira', 'uri')
    config.filter_id = config_parser.get('Jira', 'filterid')
    
    config.smtp_server = config_parser.get('Email', 'smtp_server')
    config.smtp_port = config_parser.getint('Email', 'smtp_port')
    config.smtp_login = config_parser.getboolean('Email', 'smtp_login')
    config.email_sender = config_parser.get('Email', 'user')
    config.email_password = config_parser.get('Email', 'password')
    config.sms_id = config_parser.get('Email', 'sms_id')
    config.support_id = config_parser.get('Email', 'support_id')
    config.dev_id = config_parser.get('Email', 'dev_id')
    config.phone_escl_id = config_parser.get('Email', 'phone_escl')
    
    config.mongohost  = config_parser.get('Mongo', 'host')
    config.mongoport  = config_parser.getint('Mongo', 'port')
    config.mongo_max_retry = config_parser.getint('Mongo', 'max_retry')
    config.mongo_database = config_parser.get('Mongo', 'database')
    
    config.jira_sleep_time  = config_parser.getint('Monitors', 'jira_sleep')
    config.jira_max_errors  = config_parser.getint('Monitors', 'jira_max_errors')
    config.sms_sleep_time = config_parser.getint('Monitors', 'sms_sleep')
    config.sms_max_errors  = config_parser.getint('Monitors', 'sms_max_errors')
    config.email_sleep_time = config_parser.getint('Monitors', 'email_sleep')
    config.email_max_errors  = config_parser.getint('Monitors', 'email_max_errors')
    
    config.admin_email = config_parser.get('Admin', 'admin_email')
    config.admin_sms = config_parser.get('Admin', 'admin_sms')
    
    config.twilio_account_sid = config_parser.get('Twilio', 'account_sid')
    config.twilio_account_token = config_parser.get('Twilio', 'account_token')
    config.twilio_caller_id = config_parser.get('Twilio', 'caller_id')
    config.twilio_sms_notifs = config_parser.get('Twilio', 'sms_notifs')
    config.twilio_callback_url = config_parser.get('Twilio', 'callback_url')
    config.twilio_phone_escl = config_parser.get('Twilio', 'phone_escl')
    
    config.webserver_host = config_parser.get('Webserver', 'host')
    config.webserver_port = config_parser.getint('Webserver', 'port')
    
    logger.info('Config read')
    return config
