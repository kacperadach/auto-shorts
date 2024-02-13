import requests


# TODO: add HMAC secret
def subscribe_to_channel(
    channel_id,
    lease_seconds=864000,
    callback_url="https://backend-dot-autoshorts-412215.uc.r.appspot.com/v1/youtube-webhook",
    mode="subscribe",
):
    hub_url = "https://pubsubhubbub.appspot.com/subscribe"
    topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"
    data = {
        "hub.mode": mode,
        "hub.topic": topic_url,
        "hub.callback": callback_url,
        "hub.verify": "async",
        "hub.lease_seconds": lease_seconds,
    }
    return requests.post(hub_url, data=data, timeout=30000)


if __name__ == "__main__":
    # Example usage
    response = subscribe_to_channel(
        "UCZe2MISfXymQzwJjgW8d81w",
        "https://backend-dot-autoshorts-412215.uc.r.appspot.com/v1/youtube-webhook",
    )
    print(response.status_code)
