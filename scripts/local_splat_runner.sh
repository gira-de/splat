#!/bin/bash

IMAGE="splat-local:$(date +%s)-$RANDOM"

# Restore ownership if a previous run was aborted:
sudo chown `id -u`:`id -g` -R test-project

MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')

cd test-project/

git fetch --all
git reset --hard origin/$MAIN_BRANCH
git switch $MAIN_BRANCH


cd ../

# We need to change the ownership of the test-project to match the user
# that the container is running as:
sudo chown 1001:1001 -R test-project

if ! command -v docker &> /dev/null
then
    echo "Docker could not be found. Please install Docker."
    exit
fi

docker build . -t ${IMAGE} && \
   docker run -it \
   -v $(pwd)/test-project/:/home/splatuser/test-project/ \
   -v $(pwd)/splat.yaml:/splat/splat.yaml \
   ${IMAGE} \
    python3 -m splat --project /home/splatuser/test-project

# Restore ownership:
sudo chown `id -u`:`id -g` -R test-project

# Clean up working copy:
cd test-project/
git clean -f
git reset --hard

cd ../

echo ""
echo "===================================="
echo "Splat finished. You can now inspect the changes made by splat via:

cd test-project/
git log
"
