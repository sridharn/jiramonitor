#!/usr/bin/python

import confighelper
from datetime import datetime
import jirahelpers
import logging
import mongohelper

module = 'createschedules'
logger = logging.getLogger(module)

class Schedule(object):
    def __init__(self, primary, start_date, end_date, backups):
        self.primary = primary
        self.start_date = start_date
        self.end_date = end_date
        self.backups = backups

def main():
    logger.info('%s started' % (module))
    config = confighelper.get_config()
    logger.info('Obtained config')
    logger.debug(config.__dict__)
    mongohelper.initialize(config)
    logger.info('Mongo initialized')
    mongohelper.upsert_schedules(config, get_schedules_from_files('groups.txt','schedules.txt'))
    
def get_schedules_from_files(groupfile, schedulefile):
    groups = {}
    with open(groupfile, 'r') as f:
        for line in f:
            logger.debug('Processing %s' % (line))
            group = line.replace("\n","").split(',')
            groups[group[0].strip()]=[elem.strip() for elem in group[1:len(group)]]
    schedules = []
    with open(schedulefile, 'r') as f:
        for line in f:
            schedule = line.split(',')
            primary = schedule[0].strip()
            start_date = datetime.strptime(schedule[1].strip(),'%Y/%m/%d')
            end_date = datetime.strptime(schedule[2].strip(),'%Y/%m/%d')
            backups = get_backups(groups[schedule[3].strip()], primary)
            curr_schedule = Schedule(primary,
                                     start_date,
                                     end_date,
                                     backups)
            schedules.append(curr_schedule)
    return schedules 

def get_backups(members, primary):
    memlength = len(members)
    backups = []
    logger.debug('Getting backup of "%s" in %s' % (primary, members.__str__()))
    position = members.index(primary)
    x = 0
    for i in range(memlength):
        position = position + 1
        backups.append(members[position%memlength])
    logger.debug("Backups of %s is %s" % (primary, backups.__str__()))
    return backups
    
if __name__ == '__main__':
    logfilename = module+'.log'
    logging.basicConfig(filename=logfilename, level=logging.ERROR)
    main()
