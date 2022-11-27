#! /bin/bash
target_branch=$1
echo "${target_branch}"

# Down the docker-compose first
echo "docker compose down"
docker compose down

# Remove existing images
echo "Removing docker images first"
docker rmi intermediate_api:develop

# Switch to target branch in case we're not in the right branch
echo "Changing to ${target_branch} branch"
git checkout ${target_branch}

# To pull latest version
echo "Pulling latest info from ${target_branch} branch"
git pull

# Set the Time
export TZ=NZ
export BUILD_DATE=$(date +%Y-%m-%d)-$(date +%T)

# Get the latest git commit's hash
export GIT_SHA=$(git rev-parse --short HEAD)

# Then create one
echo "Dockerizing"
echo "docker compose build --build-arg BRANCH_NAME=${target_branch} --no-cache"
docker compose build --build-arg BRANCH_NAME=${target_branch} --no-cache

# Up the docker compose in background
echo "docker compose up"
docker compose up -d
