import traceback
import queueHandler
import time
import urllib.request
from db import get_database
from bson.objectid import ObjectId
from inference_realesrgan import supre_resolution 
from signal_handler import SignalHandler
import logging
from slack_logger import SlackHandler, SlackFormatter
from datetime import datetime

sh = SlackHandler(
    'https://hooks.slack.com/services/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')
sh.setFormatter(SlackFormatter())
logging.basicConfig(handlers=[sh])
logging.getLogger().setLevel(logging.INFO)

db = get_database()

jobModel = db['jobs']
mediaModel = db['media']


def update_job_status(job_id, status, current_status):
    update_data = {'status': status}
    if status == 'DONE':
        update_data['finishedAt'] = datetime.utcnow()

    if current_status is not None and current_status == 'CREATED':
        update_data['startedAt'] = datetime.utcnow()

    jobModel.find_one_and_update(
        {'job_id': ObjectId(job_id)},
        {'$set': update_data}
    )


if __name__ == "__main__":
    signal_handler = SignalHandler()
    me = False
    while not signal_handler.received_signal:
        # me ^= True
        queueHandler.init(me)
        data = queueHandler.receive()

        if data is not None:
            job_id = data['MessageAttributes']['job_id']['StringValue']
            job = jobModel.find_one({'job_id': ObjectId(job_id)})
            media_count = data['MessageAttributes']['media_count']['StringValue']
            logging.info("Job started: %s", job_id)

            update_job_status(job_id, 'PROCESSING', job['status'])

            new_timeout = int(media_count) * 3
            queueHandler.change(data['ReceiptHandle'], new_timeout)

            images = mediaModel.find({'_id': {'$in': job['media']}})

            upscale_type = "1x"

            if 'upscale_type' in job['options']:
                upscale_type = job['options']['upscale_type']
            
            for image in images:
                try:
                    startTime = time.time()
                    resp = supre_resolution(image['url'],upscale_type)
                    endTime = time.time()
                    logging.info("Time taken for denoise: %s",
                                 str(endTime - startTime))
                    logging.info("Image Processed Upscale: %s", image['_id'])
                    
                    mediaModel.find_one_and_update(
                        {'_id': ObjectId(image['_id'])},
                        {'$set': {'output_url': resp}}
                    )
                except Exception as e:
                    logging.error(str(e))
                    logging.error("Image Processing Failed: %s", image['_id'])
                    traceback.print_exc()
                    mediaModel.find_one_and_update(
                        {'_id': ObjectId(image['_id'])},
                        {
                            '$set': {
								'status':'ERROR',
                                'error_code': '005',
                                'error': 'Error processing image',
                            }
                        }
                    )
            
            # if (not me):
            update_job_status(job_id, 'DONE', None)
            
            logging.info("Job Finished: %s", job_id)
            queueHandler.delete(data['ReceiptHandle'])
