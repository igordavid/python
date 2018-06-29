#!/usr/bin/python
# Cloudhowto 2016
# Script will list all instances which does not have certain tag
# Usage: ./script TAG_KEY_NAME 
# .. where TAG_NAME is tag which we want to check against. For example, 
# if we put "./script Environment", script will find all instances with this tag and also all instances WITHOUT this tag key. 
# It will list all stopped and running instances without this TAG_KEY_NAME, so we can see which one are without it.



import boto
from boto.ec2 import EC2Connection
import sys
from sys import argv, stdin
from time import gmtime,strftime
from boto.sns import connect_to_region
from email.mime.text import MIMEText
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

CUR_DIR=os.getcwd()

# function for checking instances

def list_instances():
    cur_time = strftime("%Y %m %d %H %M UTC",gmtime())
    main_message = "TAG REPORT for %s\n\n" % cur_time

    conn = EC2Connection()
    reservations = conn.get_all_instances()
    searching_tag = str(sys.argv[1])

# We will have few groups of instances and we are storing each of them into separated array of arrays

    missing_tag_running = []
    missing_tag_stopped = []
    having_tag_running = []
    having_tag_stopped = []
    total_instances = []
    instances_without_name_tag = []
    instances_with_empty_project = []

# Looping through all instances and then checking if they have desired tag or no

    for i in reservations:
        for inst in i.instances:
            try:
                a = inst.tags['Name']
            except:
                instances_without_name_tag.append([inst.id,inst.state])
            else:
                total_instances.append([inst.id,inst.tags['Name'],inst.state])

                if inst.tags['Project'] == "":
                    instances_with_empty_project.append([inst.id,inst.tags['Name'],inst.state,inst.tags])
                if searching_tag in inst.tags:

                    if inst.state == "running":
                        having_tag_running.append([inst.id,inst.tags['Name'],inst.state])
                    elif inst.state == "stopped":
                        having_tag_stopped.append([inst.id,inst.tags['Name'],inst.state,inst.tags])
                else:
                    if inst.state == "running":
                        missing_tag_running.append([inst.id,inst.tags['Name'],inst.state,inst.tags])
                    else:
                        missing_tag_stopped.append([inst.id,inst.tags['Name'],inst.state,inst.tags])
    main_message = main_message + "Total number of EC2 instances: %s\n" % (len(total_instances))
    print "Total number of EC2 instances: %s\n" % (len(total_instances))

####   Stopped instances without tag
    print "\nStopped EC2 instances without tag %s: %s\n" % (searching_tag,len(missing_tag_stopped))
    main_message = main_message + "\nStopped EC2 instances without tag %s (%s):\n" % (searching_tag,len(missing_tag_stopped))
    for i in missing_tag_stopped:
        main_message = main_message + "\n%s,%s\n" % (i[0].encode('utf-8'),i[2].encode('utf-8'))

        tags = i[3]
        for j in tags:
            main_message = main_message + "%s:%s\n" % (j,tags[j])
        main_message = main_message + "\n\n"

#####   Running instances without tag

    main_message = main_message + "\nRunning EC2 instances without tag %s (%s):\n" % (searching_tag,len(missing_tag_running))
    print "\nNumber of running EC2 instances without tag %s: %s\n" % (searching_tag,len(missing_tag_running))

    for i in missing_tag_running:
        main_message = main_message + "\n%s,%s\n" % (i[0].encode('utf-8'),i[2].encode('utf-8'))
        tags = i[3]
        for j in tags:
            main_message = main_message + "%s:%s\n" % (j,tags[j])
        main_message = main_message + "\n\n"
#####


####    Instances without names

    if len(instances_without_name_tag) > 0:

        main_message = main_message + "\nEC2 instances without Name tag (%s):\n" % (len(instances_without_name_tag))
        print "\nEC2 instances without Name tag (%s):\n" % (len(instances_without_name_tag))
        for i in instances_without_name_tag:
            main_message = main_message + "\n%s,%s\n" % (i[0].encode('utf-8'),i[1].encode('utf-8'))
            print i[0]
            print i[1]
#####
    

####    Instances with empty Project tag

    main_message = main_message + "\nEC2 instances with empty Project tag (%s):\n" % (len(instances_with_empty_project))
    print "\nEC2 instances with empty Project tag (%s):\n" % (len(instances_with_empty_project))
    for i in instances_with_empty_project:
        main_message = main_message + "\n%s,%s\n" % (i[0].encode('utf-8'),i[2].encode('utf-8'))
        #print i[3]
        tags = i[3]
        for j in tags:
            main_message = main_message + "%s:%s\n" % (j,tags[j])
        main_message = main_message + "\n\n"

# sending SNS notification

    subject = "Project TAG report"
    device = "arn:aws:sns:us-east-1:123456789:YOUR-SNS-TOPIC"
    c = connect_to_region('us-east-1')
    c.publish (message=main_message,subject=subject,target_arn=device)


# Saving output to /reports/timedate file and then sending e-mail/attachment

    me = "reports@CHANGE-TO-YOUR-DOMAIN"
    you = ["first_email@CHANGE-TO-YOUR-DOMAIN", "second_email@CHANGE-TO-YOUR-DOMAIN"]

    cur_time_tag = strftime("%Y-%m-%d-%H-%M",gmtime())
    write_file='%s/tagging/reports/%s.txt' % (CUR_DIR,cur_time_tag)
    write_file2 = open(write_file,"w")
    write_file2.write(main_message)
    write_file2.close()


    msg = MIMEMultipart()
    f = file(write_file)
    part = MIMEText(f.read())
    part.add_header('Content-Disposition','attachment',filename="tag-report.txt")
    msg.attach(part)

#adding body
    open_file='%s/tagging/reports/%s.txt' % (CUR_DIR,cur_time_tag)
    body=open(open_file,"r")
    msg.attach(MIMEText(main_message, 'plain'))
    body.close()

    msg['Subject'] = "Project Tag report"
    msg['From'] = me
    msg['To'] = ", ".join(you)
    s = smtplib.SMTP('localhost')
    s.sendmail(me,you,msg.as_string())
    s.quit()
    write_file2.close()

if len(sys.argv) < 2:
    print "usage: list-instances TAG_NAME"
else:
    list_instances()
