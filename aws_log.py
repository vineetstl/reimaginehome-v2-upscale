#!/usr/local/bin/python3

import boto3
import time


logs = boto3.client('logs')

LOG_GROUP = 'MagicBox'
LOG_STREAM = 'ADE'

# logs.create_log_group(logGroupName=LOG_GROUP)
# logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)


timestamp = int(round(time.time() * 1000))

response = logs.put_log_events(
    logGroupName=LOG_GROUP,
    logStreamName=LOG_STREAM,
    logEvents=[
        {
            'timestamp': timestamp,
            'message': time.strftime('%Y-%m-%d %H:%M:%S')+'\tHello world, here is our first log message!'
        }
    ]
)

print(response)