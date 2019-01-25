ORCA is a tool to control your AWS environment via GUI written in web.py

You can use it to stop or start EC2 instances based on Spot pricing.

Instructions:

1) Generate SSL cert and key and name them "server.crt" and "server.key":

openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365

2) Populate requirements from your AWS account (AWS subnet, key, iam profile..) in index.py

3) Run it via "python index.py" which will launch server on https://localhost:8080
