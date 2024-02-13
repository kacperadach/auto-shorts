import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import datetime

TASK_HANDLER_URL = "https://api.autorepurpose.com"
PROJECT = "autoshorts-412215"
LOCATION = "us-central1"
QUEUE = "SubscriptionQueue"

client = tasks_v2.CloudTasksClient()
queue_path = client.queue_path(PROJECT, LOCATION, QUEUE)


def enqueue_task(api_path: str, payload: dict, schedule_time: datetime.datetime = None):
    # Set the URL of the handler
    url = f"{TASK_HANDLER_URL}/{api_path}"

    # Construct the request body
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }

    # If a schedule time is provided, convert it to a protobuf timestamp
    if schedule_time:
        # Convert datetime to protobuf timestamp
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(schedule_time)
        task["schedule_time"] = timestamp

    response = client.create_task(request={"parent": queue_path, "task": task})
    print("Task created:", response.name)


def enqueue_channel_subscription(channel_id: str, delay=0):
    print(f"Enqueueing subscription for {channel_id}")

    schedule_datetime = None
    if delay > 0:
        schedule_datetime = datetime.datetime.now() + datetime.timedelta(seconds=delay)

    enqueue_task("v1/youtube-webhook/subscribe", {"channel_id": channel_id}, schedule_datetime)
