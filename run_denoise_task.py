import json
import traceback
import queueHandler
import time
import boto3
from inference_realesrgan import supre_resolution
from signal_handler import SignalHandler
import logging
from db import get_database
from slack_logger import SlackHandler, SlackFormatter

sh = SlackHandler(
    "https://hooks.slack.com/services/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"
)
sh.setFormatter(SlackFormatter())
logging.basicConfig(handlers=[sh])
logging.getLogger().setLevel(logging.INFO)

tablename = "reimagine-downloads"
download_table = boto3.resource("dynamodb").Table(tablename)

db = get_database()

downloadModel = db['downloads']

def update_job_status(variant_id, status,version):
    update_data = {}
    set_string = ""
    if status == "DONE":
        if version == "v1":
            set_string = "SET job_status = :status, updated_at = :ut"
            update_data = {
                ":status": status,
                ":ut": round(time.time() * 1000),
            }
        else:
            update_data = {
                "job_status" : status,
                "finishedAt" : round(time.time() * 1000),
            }

    if status == "PROCESSING":
        if version == "v1":
            set_string = "SET job_status = :status, started_at = :ut"
            update_data = {
                ":status": status,
                ":ut": round(time.time() * 1000),
            }
        else:
            update_data = {
                "job_status" : status,
                "startedAt" : round(time.time() * 1000),
            }

    if version == "v1":
        try:
            download_table.update_item(
                Key={"variant_id": variant_id},
                UpdateExpression=set_string,
                ConditionExpression="attribute_exists(variant_id)",
                ExpressionAttributeValues=update_data,
            )
        except Exception as e:
            print(e)
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logging.error("ConditionalCheckFailedException while updating record")
    else:
        downloadModel.find_one_and_update(
        {'variant_id': variant_id},
        {'$set': update_data}
        )


if __name__ == "__main__":
    signal_handler = SignalHandler()
    while not signal_handler.received_signal:
        data = queueHandler.receive()

        if data is not None:
            body = data["Body"]
            job = json.loads(body)
            variant_id = job["variant_id"]

            version = "v1"

            if "version" in job:
                version = job["version"]

            update_job_status(variant_id, "PROCESSING", version)

            new_timeout = 15
            queueHandler.change(data["ReceiptHandle"], new_timeout)

            image = ""

            upscale_type = "2x"

            if "type" in job:
                upscale_type = job["type"]
            
            

            try:
                startTime = time.time()
                resp = supre_resolution(job["input_url"], upscale_type)
                endTime = time.time()

                if version == "v1":
                    try:
                        download_table.update_item(
                            Key={"variant_id": variant_id},
                            UpdateExpression="SET output_url = :data",
                            ConditionExpression="attribute_exists(variant_id)",
                            ExpressionAttributeValues={":data": resp},
                        )
                    except Exception as e:
                        print(e)
                        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                            logging.error(
                                "ConditionalCheckFailedException while updating record"
                            )
                else:
                    downloadModel.find_one_and_update(
                        {'variant_id': variant_id},
                        {'$set': {'output_url': resp}}
                    )

            except Exception as e:
                logging.error(str(e))
                logging.error("Image Processing Failed")
                traceback.print_exc()
                update_job_status(variant_id, "ERROR", version)

            update_job_status(variant_id, "DONE", version)
            queueHandler.delete(data["ReceiptHandle"])
