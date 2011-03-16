#!/usr/bin/python

import datetime
import emailmonitor
import jirahelpers
import jiramonitor
import smsmonitor

module = 'jirascheduler'
logfilename = module+'.log'
logging.basicConfig(filename=logfilename, level=logging.ERROR)
logger = logging.getLogger(module)

def main():
    now = datetime.datetime.now().minute
    logger.info('Get config')
    config = jirahelpers.get_config()
    logger.info('Obtained config')
    jiramonitor.main(config)
    
if __name__ == '__main__':
    main()
    
    