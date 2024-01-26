## Build Docker Image

docker build -t cloud_run_repurpose .

## Tag and Push to Docker Hub
<!-- 
docker tag cloud_run_repurpose kacperadach615/cloud_run_repurpose:{version}

docker login

docker push kacperadach615/cloud_run_repurpose:{version} -->

gcloud auth configure-docker

docker tag cloud_run_repurpose gcr.io/autoshorts-412215/cloud_run_repurpose:{version}

docker push gcr.io/autoshorts-412215/cloud_run_repurpose:{version}