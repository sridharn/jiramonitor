#!/usr/bin/python

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
    
def seed_users(config, users):
    logger.info('In seed_users with %d users' % (len(users)))
    if not connection:
        logger.info('not initialized')
        initialize(config)
    for user in users:
        usercollection.save({'_id':user.jiraid,
                             'firstname':user.firstname,
                             'lastname':user.lastname,
                             'email':user.email,
                             'cell':user.cell})            

def upsert_schedules(config, schedules):
    logger.info('In upsert_schedules')
    if not connection:
        logger.info('not initialized')
        initialize(config)
    for schedule in schedules:
        schedulecollection.save({'_id':get_schedule_id(schedule.start_date, schedule.end_date),
                                 'primary':schedule.primary,
                                 'start_date':schedule.start_date,
                                 'end_date':schedule.end_date,
                                 'backups':schedule.backups})

def get_schedule_id(start_date, end_date):
    return datetime.strftime(start_date,'%Y/%m/%d')+datetime.strftime(end_date,'%Y/%m/%d')
    

def initialize(config):
    """Some mongodb initialization like establish connection, ensure the collection with its index etc"""
    global connection, database, smscollection, issuescollection, usercollection, schedulecollection
    host, port, maxretrycount, database = config.mongohost, config.mongoport, config.mongo_max_retry, config.mongo_database 
    retry_count = 1
    logger.info('Initializing mongo with %s %d %d' % (host, port, maxretrycount))
    while retry_count < maxretrycount:
        try:
            connection = pymongo.Connection(host,port)
            database = connection[database]
            smscollection = database.smslist
            issuescollection = database.jiralist
            usercollection = database.userlist
            schedulecollection = database.schedules
            logcollection = database.log
            #smscollection.ensure_index([("_id", pymongo.ASCENDING)], unique=True)
            smscollection.ensure_index([("_id", pymongo.ASCENDING)], unique=True)
            smscollection.ensure_index([("smsSent", pymongo.ASCENDING)], sparse=True)
            issuescollection.ensure_index("status")
            #schedulescollection.ensure_index([('start_date', pymongo.ASCENDING), ('end_date', pymongo.ASCENDING)], unique=True)
            return
        except:
            retry_count += 1
    raise CannotConnectToMongo(max_retry_count)

def get_new_issue(config):
    logger.info('In get new issue')
    if not connection:
        logger.info('not initialized')
        initialize(config)
    issue = smscollection.find_and_modify(query={"sms_sent":False},update={"$unset":{"sms_sent":1}, "$set":{"sms_notified":datetime.now()}})
    return issue
    
def store_issues_to_mongo(config, issues):
    if connection == None:
        logger.debug("not initialized")
        initialize(config)
    insert_issues_to_smscollection(config, issues)
    insert_issues_to_issuescollection(config, issues)

def insert_issues_to_smscollection(config, issues):
    if connection == None:
        logger.debug("not initialized")
        initialize(config)
    for issue in issues:
        issue_doc = ({"_id":issue.key,
                       "sms_sent":False, 
                       "jiraCreationTime":issue.created,
                       "sms_notified":issue.created, 
                       "priority":issue.priority, 
                       "reporter": issue.reporter,
                       "assignee": issue.assignee,
                       "company": issue.company,
                       "jiraid": issue.jiraid})
        smscollection.insert(issue_doc)
    
def insert_issues_to_issuescollection(config, issues):
    """ JIRA statuses
    1 - Open
    3 - In progress
    4 - Reopened
    5 - Resolved
    6 - Closed
    """
    if connection == None:
        logger.debug("not initialized")
        initialize(config)
    for issue in issues:
        issue_doc = ({"_id":issue.key,
                      "jiraCreationTime":issue.created,
                      "priority":issue.priority, 
                      "reporter": issue.reporter, 
                      "status" : issue.status, 
                      "assignee": issue.assignee,
                      "company" : issue.company, 
                      "summary" : issue.summary,
                      "jiraid": issue.jiraid})
        issuescollection.save(issue_doc)

def get_unassigned_issues(config):
    """get list of unassigned jira issues. status=1."""
    
    if connection == None:
        logger.debug("not initialized")
        initialize(config)
    issues = []
    for issue in issuescollection.find({'status':unassignedstatus}):
        issues.append(issue)
        logger.debug('added issue '+issue.__str__())
    return issues

def get_issues_to_escalate(config, timedelta):
    """get list of unassigned jira issues that have a creation time timedelta before."""
    
    if connection == None:
        logger.debug("not initialized")
        initialize(config)
    issues = []
    currenttime = datetime.utcnow()
    escalatetime = currenttime - timedelta
    for issue in issuescollection.find({'status':unassignedstatus, 
                                        'jiraCreationTime' : {'$lt':escalatetime}, 
                                        'escalated' : {'$exists' : False}}):
        issues.append(issue)
        logger.debug('added issue '+issue.__str__())
    return issues

def mark_issues_as_escalated(config, issues):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    issuescollection.update({'_id' : {'$in' : [issue['_id'] for issue in issues]}}, 
                            {'$set' : {'escalated' : True}})

def get_10gen_commenters(config):
    if connection == None:
        logger.debug("not initialized")
        initialize(config)
    commenters = []
    for commenter in usercollection.find({},{'_id':1}):
        commenters.append(commenter['_id'])
    return set(commenters)

def set_inprogress(config, issueid):
    if connection == None:
        logger.debug("not initialized")
        initialize(config)
    issuescollection.find_and_modify(query={"_id":issueid},update={"$set":{"status":3}})


def remove_ticket(config, issueid):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    issuescollection.remove({'_id':issueid})
    
def get_oncall_sms_nos(config):
    if connection == None:
        logger.debug("not initialized")
        initialize(mongohost, mongoport, maxretrycount)
    curr_date = datetime.utcnow()
    sms_numbers = []
    for oncall in schedulecollection.find(
                                            {'start_date':{'$lt':curr_date},
                                             'end_date':{'$gt':curr_date}}
                                            ):
        people = oncall['backups']
        logger.debug('On calls are %s'%(people.__str__()))
        for person in usercollection.find({'_id':{'$in':people}}):
            sms_numbers.append(person['cell'])
    return sms_numbers


        
    