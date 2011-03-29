#!/usr/bin/python

from bottle import route, run
import datetime
import jirahelpers
import logging
import mongohelper
import twilio

module = 'twilioresponder'
logger = logging.getLogger(module)
logfilename = module+'.log'
logging.basicConfig(filename=logfilename, level=logging.ERROR)

timedelta = datetime.timedelta(minutes=50)

@route('/', method='POST')
@route('/index.html', method='POST')
@route('/index.htm', method='POST')
def index():
    return do()

@route('/voicemail')
def index():
    response = ["<?xml version='1.0' encoding='utf-8' ?>\n"]
    r = twilio.Response()
    s = twilio.Say('Hello, Thank you for calling 10 jen. 10 jen develops and provides enterprise grade support for Mongo D B.')
    r.append(s)
    s = twilio.Say(' And oh yes', voice = twilio.Say.WOMAN)
    r.append(s)
    r.append(twilio.Pause())
    s = twilio.Say(' Mongo D B is web scale', voice = twilio.Say.WOMAN)
    r.append(s)
    return r.__repr__()
    
def do():
    try:
        logger.info('In do')
        config = jirahelpers.get_config()
        logger.info('Obtained config')
        response = ["<?xml version='1.0' encoding='utf-8' ?>\n"]
        r = twilio.Response()
        issues = mongohelper.get_issues_to_escalate(config.mongohost, 
                                                    config.mongoport, 
                                                    config.mongo_max_retry, 
                                                    timedelta)
        if len(issues) > 0:
            say_msg = ['The following issues have been opened for at least 50 minutes']
            for issue in issues:
                say_msg.append(', ')
                say_msg.append(issue['_id'])
            s = twilio.Say(''.join(say_msg))
            mongohelper.mark_issues_as_escalated(config.mongohost, 
                                                config.mongoport, 
                                                config.mongo_max_retry,
                                                issues)
        else:
            s = twilio.Say('All escalations have been taken care of')
        r.append(s)
        response.append(r.__repr__())
        return ''.join(response)
    except Exception, e:
        logger.warning(e)

if __name__ == "__main__":
    config = jirahelpers.get_config()
    run(host=config.webserver_host, port=config.webserver_port)
    