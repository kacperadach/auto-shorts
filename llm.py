import os

import requests
from pydantic import BaseModel


RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_URL = "https://api.runpod.ai/v2/llama2-13b-chat/run"
RUNPOD_STATUS_URL = "https://api.runpod.ai/v2/llama2-13b-chat/status/"


# {
#     "input": {
#         "prompt": "Who is the president of the United States?",
#         "sampling_params": {
#             "max_tokens": 100,
#             "n": 1,
#             "presence_penalty": 0.2,
#             "frequency_penalty": 0.7,
#             "temperature": 0.3,
#         },
#     }
# }


class LlamaSamplingParams(BaseModel):
    max_tokens: int = 100
    n: int = 1
    presence_penalty: float = 0.2
    frequency_penalty: float = 0.7
    temperature: float = 0.3


class LlamaInput(BaseModel):
    prompt: str
    sampling_params: LlamaSamplingParams


class RunpodLlamaBody(BaseModel):
    input: LlamaInput


def call_llama_runpod(prompt: str):
    body = RunpodLlamaBody(
        input=LlamaInput(prompt=prompt, sampling_params=LlamaSamplingParams())
    )
    response = requests.post(
        RUNPOD_URL,
        json=body.dict(),
        headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
        timeout=30000,
    )
    print(response.json())
    return response.json()


def get_llama_status_runpod(job_id: str):
    return requests.get(
        RUNPOD_STATUS_URL + job_id,
        headers={"Authorization": "Bearer " + RUNPOD_API_KEY},
        timeout=30000,
    ).json()
