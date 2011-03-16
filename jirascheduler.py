#!/usr/bin/python

import datetime
import emailmonitor
import jirahelpers
import jiramonitor
import logging
import smsmonitor

module = 'jirascheduler'
logfilename = module+'.log'
logging.basicConfig(filename=logfilename, level=logging.ERROR)
logger = logging.getLogger(module)

def main():
    logger.info('%s started' % (module))
    now = datetime.datetime.now().minute
    logger.info('Now %d' % (now))
    config = jirahelpers.get_config()
    logger.info('Obtained config')
    logger.debug(config.__dict__)
    jiramonitor.main(config)
    logger.info('Updated tickets')
    smsmonitor.main(config)
    logger.info('Completed SMS notifications')
    if now % 5 == 0:
        emailmonitor.main(config)
        logger.info('Completed email notifications')
    
if __name__ == '__main__':
    main()
    
    