#!/bin/env python
import boto3
import parser
import argparse

class Find_elb():

        def __init__(self,instance_id,region):
                self.instance_id = instance_id
                self.region = region

        def locate_elb(self):
                elb_client = boto3.client('elb',region_name=self.region)
                self.all_elbs = elb_client.describe_load_balancers()
                try:
                        for i in self.all_elbs['LoadBalancerDescriptions']:
                                for j in i['Instances']:
                                        if j['InstanceId'] == self.instance_id:
                                                elb_name = i['LoadBalancerName']
                                                print elb_name
                except Exception as e:
                        print "error: %s" % e



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line parser")
    parser.add_argument('-i', '--instance_id', help='instance ID', required='True')
    parser.add_argument('-r', '--region', help='region', required='True')
    args = parser.parse_args()

    find_elb = Find_elb(args.instance_id, args.region)
    find_elb.locate_elb()
