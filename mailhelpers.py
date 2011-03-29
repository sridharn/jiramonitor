import jirahelpers
import logging
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from smtplib import SMTP

module = 'mailhelper'
logger = logging.getLogger(module)

def send_mail(config, recipient_list, mimemsg):
    """Helper method to send an email of the issues where issues is a list of bson objects"""
    logger.info('Send actual email/SMS')
    mailServer = SMTP(config.smtp_server, config.smtp_port)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    if config.smtp_login: mailServer.login(config.email_sender, config.email_password)
    mailServer.sendmail(config.email_sender, recipient_list, mimemsg.as_string(False))
    mailServer.close()
    logger.info('Email/SMS sent')
    
def escalate(config, recipient_list, subject, issues):
    email_issues(config, recipient_list, subject, issues)


def email_issues(config, recipient_list, subject, issues):
    """Helper method to send an email of the issues where issues is a list of bson objects"""
    logger.info('Send email of issues')
    mailBody = formatHtmlMailBody(issues)
        
    mime_msg = MIMEMultipart('alternate')
    mime_msg['Subject'] = subject
    mime_msg['From'] = config.email_sender
    
    if isinstance(recipient_list, str):
        mime_msg['To'] = recipient_list
    else:
        mime_msg['To'] = ','.join(recipient_list)
    mime_msg.attach(MIMEText('','plain'))
    mime_msg.attach(MIMEText(mailBody,'html'))
    
    send_mail(config, recipient_list, mime_msg)
    
def sms_issue(config, issue, recipient_list):
    """Helper method to send an sms of the issue defined by the bson dictionary issue"""
    logger.info('Send sms of %s' % (issue["_id"]))
    sms_msg = MIMEMultipart()
    sms_msg['Subject'] = 'New JIRA issue %s' % (issue["_id"])
    sms_msg['From'] = config.email_sender
    if isinstance(recipient_list, str):
        sms_msg['To'] = recipient_list
    else:
        sms_msg['To'] = ','.join(recipient_list)
    sms_msg.attach(MIMEText(get_sms_body(issue)))
    
    send_mail(config, recipient_list, sms_msg)

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
    
def formatHtmlMailBody(issues):
    """Helper method to create an email body of the issues bson"""
    logger.info('In format email body')
    msg = ['<html><head></head><body><table border="1">']
    msg.append('<tr><th>Id</ht><th>Priority</th><th>Company</th><th>Reporter</th><th>Created</th><th>Description</th></tr>')
    for issue in issues:
        msg.append('<tr>')
        msg.append('<td><a href="')
        msg.append('https://jira.mongodb.org/browse/')
        msg.append(issue['_id'])
        msg.append('" title="')
        msg.append(issue['_id'])
        msg.append('">')
        msg.append(issue['_id'])
        msg.append('</a>')        
        msg.append('</td>')
        msg.append('<td>')
        msg.append(str(issue['priority']))
        msg.append('</td>')
        msg.append('<td>')
        msg.append(issue.get('company', 'Unknown'))
        msg.append('</td>')
        msg.append('<td>')
        msg.append(issue['reporter'])
        msg.append('</td>')
        msg.append('<td>')
        msg.append(issue["jiraCreationTime"].strftime('%Y/%m/%d %H:%M:%S'))
        msg.append('</td>')
        msg.append('<td>')
        msg.append(issue.get('summary'))
        msg.append('</td>')
        msg.append('</tr>')
    msg.append('</table></body></html>')
    return ''.join(msg)

def alert_admin(config, module, message):
    """Helper method to send an alert (both email and sms) when monitor dies"""
    logger.info('Send alert for '+module)
    sms_msg = MIMEMultipart()
    sms_msg['Subject'] = 'Module Failure - %s' % (module)
    sms_msg['From'] = config.email_sender
    sms_msg['To'] = config.admin_sms
    sms_msg.attach(MIMEText(''))
    
    email_msg = MIMEMultipart()
    email_msg['Subject'] = 'Module Failure - %s' % (module)
    email_msg['From'] = config.email_sender
    email_msg['To'] = config.admin_email
    email_msg.attach(MIMEText(message))
    
    send_mail(config, config.admin_sms, sms_msg)
    send_mail(config, config.admin_email, email_msg)
    
    