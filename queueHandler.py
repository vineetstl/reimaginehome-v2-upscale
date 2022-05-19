import boto3
import botocore

sqs = boto3.client('sqs')

me_queue_set = {
    'me_straighten': 'https://sqs.us-west-2.amazonaws.com/211949186043/AutoStraightenME',
    'me_enhance': 'https://sqs.us-west-2.amazonaws.com/211949186043/ImageEnhanceME',
    'me_sky_replace': 'https://sqs.us-west-2.amazonaws.com/211949186043/SkyReplaceME',
    'me_ade': 'https://sqs.us-west-2.amazonaws.com/211949186043/RecogADEME',
    'me_predict': 'https://sqs.us-west-2.amazonaws.com/211949186043/RecogPredictME',
}

queue_url = 'https://sqs.us-west-2.amazonaws.com/211949186043/DenoiseUpscale'


def init(me):
    global queue_url
    if me:
        queue_url = 'https://sqs.us-west-2.amazonaws.com/211949186043/DenoiseUpscale'
    else:
        queue_url = 'https://sqs.us-west-2.amazonaws.com/211949186043/DenoiseUpscale'



def change(receipt_handle, time):
    sqs.change_message_visibility(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle,
        VisibilityTimeout=time
    )


def receive():
    response = None
    try:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=20
        )
    except botocore.exceptions.ClientError as error:
        print(error)
        return None

    if 'Messages' in response:
        message = response['Messages'][0]
        return message
    else:
        return None


def delete(receipt_handle):
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
