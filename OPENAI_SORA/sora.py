import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
import requests
import json
import time
import uuid

load_dotenv()
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("API_VERSION")
sora_deployment_name = os.getenv("SORA_DEPLOYMENT_NAME")

path = 'openai/v1/video/generations/jobs'
params = f'?api-version={api_version}'
constructed_url = azure_openai_endpoint + path + params

headers = {
  'Api-Key': azure_openai_api_key,
  'Content-Type': 'application/json',
}

body = {
  "prompt": "generate an image of future eco sustainable city with hybrid society of humans and robots, digital art",
  "n_seconds": "5",
  "height": "480",
  "width": "854",
  "model": sora_deployment_name,
}


job_response = requests.post(constructed_url, headers=headers, json=body)
if not job_response.ok:
    print("❌ Video generation failed.")
    print(json.dumps(job_response.json(), sort_keys=True, indent=4, separators=(',', ': ')))
else:
    print(json.dumps(job_response.json(), sort_keys=True, indent=4, separators=(',', ': ')))
    job_response = job_response.json()
    job_id = job_response.get("id")
    status = job_response.get("status")
    status_url = f"{azure_openai_endpoint}openai/v1/video/generations/jobs/{job_id}?api-version={api_version}"

    print(f"⏳ Polling job status for ID: {job_id}")
    while status not in ["succeeded", "failed"]:
        time.sleep(5)
        job_response = requests.get(status_url, headers=headers).json()
        status = job_response.get("status")
        print(f"Status: {status}")

    if status == "succeeded":
        print(job_response)
        generations = job_response.get("generations", [])
        if generations:
            print(f"✅ Video generation succeeded.")

            generation_id = generations[0].get("id")
            video_url = f'{azure_openai_endpoint}openai/v1/video/generations/{generation_id}/content/video{params}'
            video_response = requests.get(video_url, headers=headers)
            if video_response.ok:
                output_filename_prefix = "output" + str(uuid.uuid4())
                output_filename = output_filename_prefix + ".mp4"
                with open(output_filename, "wb") as file:
                    file.write(video_response.content)
                print(f'Generated video saved as "{output_filename}"')
        else:
            print("⚠️ Status is succeeded, but no generations were returned.")
    elif status == "failed":
        print("❌ Video generation failed.")
        print(json.dumps(job_response, sort_keys=True, indent=4, separators=(',', ': ')))
