__author__ = 'igor david, dec 2015'
# ptss stands for "orchestration and automation"
# it will be used for performance teams starting spot instances


import sys, os
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
import web
from web import form
from threading import Timer
import boto
from boto.ec2 import EC2Connection
from boto import cloudformation
import sys
from sys import argv, stdin
import time
from time import sleep
import threading
from time import gmtime, strftime
import logging
logging.basicConfig(filename='injectors.log',level=logging.INFO)
import web
import re
import base64
import json
import boto3
import datetime
from web.wsgiserver import CherryPyWSGIServer
web.config.debug = False

# Put your values below

#######

profile_name = "" # put-your-local-boto3-profile-name
your_ami_id = "" # put-your-ami-here
your_key_name = "" # put-your-key-name-here
your_iam_profile = "" # put-your-iam-role-here
subnet_id = "" # put-your-subnet-id-here
your_snapshot_id = "" # put your snapshot ID here
groups = "" # [put-list-of-your-groups-here]
creds = "" # put your ('username','password')

#######


def csrf_token():
    if not session.has_key('csrf_token'):
        from uuid import uuid4
        session.csrf_token=uuid4().hex
    return session.csrf_token

def csrf_protected(f):
    def decorated(*args,**kwargs):
        inp = web.input()
        if not (inp.has_key('csrf_token') and inp.csrf_token==session.pop('csrf_token',None)):
            raise web.HTTPError(
                "400 Bad request",
                {'content-type':'text/html'},
                """Cross-site request forgery (CSRF) attempt (or stale browser form).
<a href="https://localhost">Back to the form</a>.""")
        return f(*args,**kwargs)
    return decorated

render = web.template.render('templates/',globals={'csrf_token':csrf_token})



CherryPyWSGIServer.ssl_certificate = "server.crt"
CherryPyWSGIServer.ssl_private_key = "server.key"

if 'threading' in sys.modules:
    del sys.modules['threading']


urls = (
    '/','index',
    '/login','Login'
)

allowed = (
    creds,
)

application = web.application(urls, globals())

if web.config.get('_session') is None:
    session = web.session.Session(application, web.session.DiskStore('sessions'))
    web.config._session = session
else:
    session = web.config._session


myform = form.Form(form.Dropdown('How Many', [
                                            ('1', 'Launch one instance'),
                                            ('2', 'Launch two instances'),
                                            ('3', 'Launch three instances'),
                                            ('4', 'Launch four instances'),
                                            ('5', 'Launch five instances'),
                                            ]))

myform2 = form.Form(form.Dropdown('Required Time', [
                                                    ('60', '1 hour'),
                                                    ('120', '2 hours'),
                                                    ('180', '3 hours'),
                                                    ('240', '4 hours'),
                                                    ('300', '5 hours'),
                                                    ('360', '6 hours'),
                                                    ]))


myform4 = form.Form(form.Dropdown('Injector', [('Instance1', 'Instance1')
                                              ]))

class index:
    def GET(self):
        current_time = strftime("%Y-%m-%d %H:%M:%S")
        form = myform()
        form2 = myform2()
        form4 = myform4()
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:
            return render.welcome(current_time, form, form2, form4)
        else:
            raise web.seeother('/login')
    @csrf_protected
    def POST(self):
        current_time = strftime("%Y-%m-%d %H:%M:%S")
        form = myform()
        form2 = myform2()
        form4 = myform4()

        if not form.validates():
            return render.welcome(current_time,form,form2,form4)
        if not form2.validates():
            return render.welcome(current_time,form,form2,form4)
        if not form4.validates():
            return render.welcome(current_time,form,form2,form4)
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:
            required_time = form2['Required Time'].value
            number_of_instances = form['How Many'].value
            instance_name_tag = form4['Injector'].value
            spot_instance_price = "0.015"
            boto3.setup_default_session(profile_name=profile_name)
            client = boto3.client('ec2')
            response = client.request_spot_instances(
    SpotPrice='0.099',
    InstanceCount=int(number_of_instances),
    Type='one-time',
    BlockDurationMinutes=int(required_time),
    LaunchSpecification={
        'ImageId': 'your_ami_id',
        'KeyName': your_key_name,
        'InstanceType': 'm3.large',
        'BlockDeviceMappings': [
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'SnapshotId': your_snapshot_id,
                    'VolumeSize': 20,
                    'DeleteOnTermination': True,
                    'VolumeType': 'gp2',
                    'Encrypted': False
                },

            },
        ],
        'NetworkInterfaces': [
            {
                'DeviceIndex': 0,
                'AssociatePublicIpAddress': True,
                'SubnetId': subnet_id,
                'Groups': groups,
            }
        ],
        'IamInstanceProfile': {
            'Arn': your_iam_profile
        },
        'EbsOptimized': False,
        'Monitoring': {
            'Enabled': False
        }
    }
)

            num_of_request_ids = int(len(response['SpotInstanceRequests']))
            sir_request_ids = []
            timer = 0
            for i in range(0,num_of_request_ids):
                sir_request_ids.append(response['SpotInstanceRequests'][i]['SpotInstanceRequestId'])
            sir_request_id = response['SpotInstanceRequests'][0]['SpotInstanceRequestId']
            sir_status = client.describe_spot_instance_requests(
                SpotInstanceRequestIds=[sir_request_id])['SpotInstanceRequests'][0]['Status']['Code']
            while (str(sir_status) != "fulfilled"):
                sir_status = client.describe_spot_instance_requests(
                SpotInstanceRequestIds=[sir_request_id])['SpotInstanceRequests'][0]['Status']['Code']
                time.sleep(10)
                timer = timer + 10
                if (sir_status == "fulfilled"):
                    sir_full_details = []
                    for i in sir_request_ids:
                        sir_details = client.describe_spot_instance_requests(
                SpotInstanceRequestIds=[i])
                        sir_full_details.append(sir_details)

                elif (sir_status == "price-too-low"):
                    client.cancel_spot_instance_requests(
                            SpotInstanceRequestIds=[sir_request_id])
                    return render.price_too_low(offer)
                elif (timer > 300):
                    client.cancel_spot_instance_requests(
                            SpotInstanceRequestIds=[sir_request_id])
                    return render.waiting_too_long(timer)
            all_instance_details = []
            for i in sir_full_details:
                instance_id = i['SpotInstanceRequests'][0]['InstanceId']
                instance_details = client.describe_instances(InstanceIds=[instance_id])
                all_instance_details.append(instance_details)
                instance_ip = client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['PrivateIpAddress']
                client.create_tags(Resources=[instance_id],Tags=[{'Key':'Name','Value':instance_name_tag},{'Key':'Project','Value':'Performance QA'},
                                                                 {'Key':'Technical Owner','Value':'Igor David'}])

            return render.result(required_time,number_of_instances,all_instance_details)

        else:
            raise web.seeother('/login')
            tip = type(num_of_request_ids)
            tipsirfull = type(sir_full_details)
            spot_instance_price = "0.015"


class Login:
    def GET(self):
        auth = web.ctx.env.get('HTTP_AUTHORIZATION')
        authreq = False
        if auth is None:
            authreq = True
        else:
            auth = re.sub('^Basic ','',auth)
            username,password = base64.decodestring(auth).split(':')
            if (username,password) in allowed:
                raise web.seeother('/')
            else:
                authreq = True
        if authreq:
            web.header('WWW-Authenticate','Basic realm="Authentication required"')
            web.ctx.status = '401 Unauthorized'
            return


if __name__=="__main__":
	web.internalerror = web.debugerror
	application.run()
