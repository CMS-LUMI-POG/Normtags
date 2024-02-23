#!/usr/bin/env python

# A  very silly script to make a leaderboard of who's done the most fill validations.

import json
from collections import defaultdict

with open('fillValidationLog.json', 'r') as validationLog:
    validationData = json.load(validationLog)

users = defaultdict(int)

for i in validationData:
    if 'validated_by' not in i:
        continue
    name = i['validated_by']
    users[name] += 1

for (k, v) in sorted(users.items(), key=lambda x: x[1], reverse=True):
    print v, k
    
