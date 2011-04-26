#!/usr/bin/python
  
import confighelper
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

class CannotConnectToJira(Exception):
    def __init__(self, count):
        self.msg = 'Cannot connect to JIRA after %d tries' % (count)
    def __str__(self):
        return self.msg

        
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
        self.assignee = issue.get('assignee')
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
           
def get_issues_by_filterid(auth, jiraproxy, filterid):
    """Get list of JIRA issues as specified by the filer id. The filter should be 
    accessible by the configured JIRA user"""
    
    logger.info('Fetching issues for filter %s' % (filterid))
    issues = jiraproxy.jira1.getIssuesFromFilter(auth, filterid)
    logger.info('Filter query returned %d issues' % (len(issues)))
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
    