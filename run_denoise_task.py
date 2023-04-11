import json
import traceback
import queueHandler
import time
import boto3
from inference_realesrgan import supre_resolution
from signal_handler import SignalHandler
import logging
from slack_logger import SlackHandler, SlackFormatter

sh = SlackHandler(
    "https://hooks.slack.com/services/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"
)
sh.setFormatter(SlackFormatter())
logging.basicConfig(handlers=[sh])
logging.getLogger().setLevel(logging.INFO)

tablename = "reimagine-downloads"
download_table = boto3.resource("dynamodb").Table(tablename)


def update_job_status(job_id, status):
    update_data = {}
    set_string = ""
    if status == "DONE":
        set_string = "SET job_status = :status, updated_at = :ut"
        update_data = {
            ":status": status,
            ":ut": round(time.time() * 1000),
        }

    if status == "PROCESSING":
        set_string = "SET job_status = :status, started_at = :ut"
        update_data = {
            ":status": status,
            ":ut": round(time.time() * 1000),
        }

    try:
        download_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=set_string,
            ConditionExpression="attribute_exists(job_id)",
            ExpressionAttributeValues=update_data,
        )
    except Exception as e:
        print(e)
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            logging.error("ConditionalCheckFailedException while updating record")


if __name__ == "__main__":
    signal_handler = SignalHandler()
    while not signal_handler.received_signal:
        data = queueHandler.receive()

        if data is not None:
            body = data["Body"]
            job = json.loads(body)
            job_id = job["job_id"]

            update_job_status(job_id, "PROCESSING")

            new_timeout = 15
            queueHandler.change(data["ReceiptHandle"], new_timeout)

            image = ""

            upscale_type = "2x"

            if "upscale" in job:
                upscale_type = job["upscale"]

            try:
                startTime = time.time()
                resp = supre_resolution(job["url"], upscale_type)
                endTime = time.time()

                try:
                    download_table.update_item(
                        Key={"job_id": job_id},
                        UpdateExpression="SET output_url = :data",
                        ConditionExpression="attribute_exists(job_id)",
                        ExpressionAttributeValues={":data": resp},
                    )
                except Exception as e:
                    print(e)
                    if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                        logging.error(
                            "ConditionalCheckFailedException while updating record"
                        )

            except Exception as e:
                logging.error(str(e))
                logging.error("Image Processing Failed")
                traceback.print_exc()
                update_job_status(job_id, "ERROR")

            update_job_status(job_id, "DONE")
            queueHandler.delete(data["ReceiptHandle"])
