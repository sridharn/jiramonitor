#!/usr/bin/python
  
import ConfigParser
import datetime
import logging
import sys
import traceback
import xmlrpclib

# Time format is "2011-02-22 18:50:33.0"
timeformat = '%Y-%m-%d %H:%M:%S.0'
module = 'jirahelper'
logger = logging.getLogger(module)
max_errors_message = 'Module %s failed since %d errors reached.'
LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

class CannotConnectToJira(Exception):
    def __init__(self, count):
        self.msg = 'Cannot connect to JIRA after %d tries' % (count)
    def __str__(self):
        return self.msg

class Config(object):
    """Class to hold config values read from OS config file"""
    def __init__(self):
        mongohost = 'localhost'
        mongoport = 27017

class Issue(object):
    """Simple class to hold basic information about JIRA issue"""
    def __init__(self, issue):
        self.key = issue['key']
        self.priority = int(issue['priority'])
        self.reporter = issue['reporter']
        self.created = datetime.datetime.strptime(issue['created'], timeformat)
        self.status = int(issue['status'])
        self.summary = issue['summary']
        self.jiraid = int(issue['id'])
        self.company = None
        customfields = issue['customFieldValues']
        for field in customfields:
            if field['customfieldId'] == 'customfield_10030':
                self.company = field['values']
    def __str__(self):
        return 'key:%s priority:%d reporter:%s created:%s status:%s' \
               % (self.key, self.priority, self.reporter, self.created, \
                  self.status)
    def url(self):
        return 'https://jira.mongodb.org/browse/' % (self.key)     

def formatExceptionInfo(maxTBlevel=5):
         cla, exc, trbk = sys.exc_info()
         excName = cla.__name__
         try:
             excArgs = exc.__dict__["args"]
         except KeyError:
             excArgs = "<no args>"
         excTb = traceback.format_tb(trbk, maxTBlevel)
         return (excName, excArgs, excTb)
     
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
    
    config.jira_sleep_time  = config_parser.getint('Monitors', 'jira_sleep')
    config.jira_max_errors  = config_parser.getint('Monitors', 'jira_max_errors')
    config.sms_sleep_time = config_parser.getint('Monitors', 'sms_sleep')
    config.sms_max_errors  = config_parser.getint('Monitors', 'sms_max_errors')
    config.email_sleep_time = config_parser.getint('Monitors', 'email_sleep')
    config.email_max_errors  = config_parser.getint('Monitors', 'email_max_errors')
    
    config.admin_email = config_parser.get('Admin', 'admin_email')
    config.admin_sms = config_parser.get('Admin', 'admin_sms')
    return config
      
def get_issues_by_filterid(auth, jiraproxy, filterid):
    """Get list of JIRA issues as specified by the filer id. The filter should be 
    accessible by the configured JIRA user"""
    
    logger.info('Fetching issues for filter %s' % (filterid))
    issues = jiraproxy.jira1.getIssuesFromFilter(auth, filterid)
    logger.info('Filter query returned %d issues' % (len(issues)))
#    issueList = []
#    for issue in issues: 
#        issue = Issue(issue["key"], 
#                      issue["priority"], 
#                      issue["reporter"], 
#                      issue["created"], 
#                      issue["status"])
#        issueList.append(issue)
    issueList = [Issue(issue) for issue in issues]
    return issueList
    
def auth_against_jira(url, user, password, maxretrycount):
    logger.info('Authenticating against JIRA with %s %s %d' %(url, user, maxretrycount))
    retry_count = 1
    while retry_count < maxretrycount:
        try:
            proxy = xmlrpclib.ServerProxy(url)
            auth = proxy.jira1.login(user, password)
            return proxy, auth
        except:
            retry_count += 1
    raise CannotConnectToJira(maxretrycount)

def get_issue_commenters(auth, jiraproxy, issueid):
    logger.info('Fetching comment for issue %s' % (issueid))
    comments = jiraproxy.jira1.getComments(auth, issueid)
    commenters = []
    for comment in comments:
        commenters.append(comment['author'])
    return set(commenters)
    