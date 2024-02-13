## Build Docker Image

docker build -t cloud_run_repurpose -f cloudrun/Dockerfile .

# On Mac

docker buildx build --platform linux/amd64 -t cloud_run_repurpose -f cloudrun/Dockerfile  .

## Tag and Push to GCR

gcloud auth configure-docker

docker tag cloud_run_repurpose gcr.io/autoshorts-412215/cloud_run_repurpose:{version}

docker push gcr.io/autoshorts-412215/cloud_run_repurpose:{version}