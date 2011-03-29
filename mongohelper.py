import logging
import pymongo 
from datetime import datetime

connection = None
database = None
smscollection = None
issuescollection = None
logcollection = None
usercollection = None
unassignedstatus = 1

module = 'mongohelper'
logger = logging.getLogger(module)
"""
use jira
db.smslist.drop()
db.jiralist.drop()
db.createCollection("smslist", {capped:true,size:100000})
db.createCollection("jiralist")
db.smslist.find()
db.jiralist.find()
"""

class CannotConnectToMongo(Exception):
    def __init__(self, count):
        self.msg = 'Cannot connect to Mongo after %d tries' % (count)
    def __str__(self):
        return self.msg
    
def initialize_and_seed(config):
    global usercollection
    initialize(config)
    usercollection = database.userlist
    with open('userlist.txt', 'r') as f:
        for line in f:
            user = line.split(',')
            logger.debug('User name=%s User id=%s' % (user[0].strip(), user[1].strip()))
            usercollection.save({'_id':user[0].strip(),'email':user[1].strip()})            

def initialize(config):
    """Some mongodb initialization like establish connection, ensure the collection with its index etc"""
    global connection, database, smscollection, issuescollection
    host, port, maxretrycount, database = config.mongohost, config.mongoport, config.mongo_max_retry, config.mongo_database 
    retry_count = 1
    logger.info('Initializing mongo with %s %d %d' % (host, port, maxretrycount))
    while retry_count < maxretrycount:
        try:
            connection = pymongo.Connection(host,port)
            database = connection[database]
            smscollection = database.smslist
            issuescollection = database.jiralist
            logcollection = database.log
            #smscollection.ensure_index([("_id", pymongo.ASCENDING)], unique=True)
            smscollection.ensure_index([("_id", pymongo.ASCENDING)], unique=True)
            smscollection.ensure_index([("smsSent", pymongo.ASCENDING)], sparse=True)
            issuescollection.ensure_index("status")
            return
        except:
            retry_count += 1
    raise CannotConnectToMongo(max_retry_count)

def get_new_issue(mongohost, mongoport, maxretrycount):
    logger.info('In get new issue')
    if not connection:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    issue = smscollection.find_and_modify(query={"sms_sent":False},update={"$unset":{"sms_sent":1}, "$set":{"sms_notified":datetime.now()}})
    return issue
    
def store_issues_to_mongo(mongohost, mongoport, maxretrycount, issues):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport)
    insert_issues_to_smscollection(mongohost, mongoport, maxretrycount, issues)
    insert_issues_to_issuescollection(mongohost, mongoport, maxretrycount, issues)

def insert_issues_to_smscollection(mongohost, mongoport, maxretrycount, issues):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    for issue in issues:
        issue_doc = ({"_id":issue.key,
                       "sms_sent":False, 
                       "jiraCreationTime":issue.created,
                       "sms_notified":issue.created, 
                       "priority":issue.priority, 
                       "reporter": issue.reporter,
                       "company": issue.company,
                       "jiraid": issue.jiraid})
        smscollection.insert(issue_doc)
    
def insert_issues_to_issuescollection(mongohost, mongoport, maxretrycount, issues):
    """ JIRA statuses
    1 - Open
    3 - In progress
    4 - Reopened
    5 - Resolved
    6 - Closed
    """
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    for issue in issues:
        issue_doc = ({"_id":issue.key,
                      "jiraCreationTime":issue.created,
                      "priority":issue.priority, 
                      "reporter": issue.reporter, 
                      "status" : issue.status, 
                      "company" : issue.company, 
                      "summary" : issue.summary,
                      "jiraid": issue.jiraid})
        issuescollection.save(issue_doc)

def get_unassigned_issues(mongohost, mongoport, maxretrycount):
    """get list of unassigned jira issues. status=1."""
    
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    issues = []
    for issue in issuescollection.find({'status':unassignedstatus}):
        issues.append(issue)
        logger.debug('added issue '+issue.__str__())
    return issues

def get_issues_to_escalate(mongohost, mongoport, maxretrycount, timedelta):
    """get list of unassigned jira issues that have a creation time timedelta before."""
    
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    issues = []
    currenttime = datetime.utcnow()
    escalatetime = currenttime - timedelta
    for issue in issuescollection.find({'status':unassignedstatus, 
                                        'jiraCreationTime' : {'$lt':escalatetime}, 
                                        'escalated' : {'$exists' : False}}):
        issues.append(issue)
        logger.debug('added issue '+issue.__str__())
    return issues

def mark_issues_as_escalated(mongohost, 
                             mongoport, 
                             mongo_max_retry,
                             issues):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    issuescollection.update({'_id' : {'$in' : [issue['_id'] for issue in issues]}}, 
                            {'$set' : {'escalated' : True}})

def get_commenters(mongohost, mongoport, mongo_max_retry):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    commenters = []
    for commenter in usercollection.find({},{'_id':1}):
        commenters.append(commenter['_id'])
    return set(commenters)

def set_inprogress(mongohost, mongoport, mongo_max_retry, issueid):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    issuescollection.find_and_modify(query={"_id":issueid},update={"$set":{"status":3}})

    
    