#!/bin/sh

REPO_ROOT_DIR=$1          # "/opt/app-root/src/demo/sgahlot-nvidia-usecase"
MODELS_DIR="$REPO_ROOT_DIR/models/tuned-toy-jensen"
# SAVED_MODEL_DIR="$MODELS_DIR/model"
MODEL_ZIP_FILE_NAME="model.zip"
MAR_MODEL_NAME="stable-diffusion"
WORKLOADS_REPO_DIR="workloads/examples/stable-diffusion-dreambooth/notebook/model"

printf "REPO_ROOT_DIR=%s\n" $REPO_ROOT_DIR

# Create zip file containing the model directory
cd $MODELS_DIR
printf "In the SAVED_MODEL_DIR - PWD=%s. Creating [%s] containing model dir\n" `pwd` $MODEL_ZIP_FILE_NAME
zip -r $MODEL_ZIP_FILE_NAME model/*

# cd ..
printf "In the MODELS_DIR - PWD=%s\n" `pwd`
mkdir -p gen-mar/archive/config
cd gen-mar

printf "Moving ../%s in the gen-mar dir\n" $MODEL_ZIP_FILE_NAME
mv ../$MODEL_ZIP_FILE_NAME .

# Clone distributed-downloads to copy config.properties and requirements.txt
printf "Cloning opendatahub-io/distributed-workloads...\n"
git clone https://github.com/opendatahub-io/distributed-workloads.git workloads

printf "Copying config.properties and requirements.txt...\n"
cp ${WORKLOADS_REPO_DIR}/config.properties archive/config
cp ${WORKLOADS_REPO_DIR}/requirements.txt .

# Install and run torch-model-archiver
printf "Installing torch-model-archiver"
pip install -q torch-model-archiver

torch-model-archiver --model-name $MAR_MODEL_NAME \
    --version 1.0 \
    --handler ${WORKLOADS_REPO_DIR}/stable_diffusion_handler.py \
    --extra-files ./$MODEL_ZIP_FILE_NAME \
    -f -r requirements.txt

mv ${MAR_MODEL_NAME}.mar archive

printf "In the gen-mar dir - PWD=%s. Files after running archiver:\n" `pwd`
find archive -type f -exec ls -lh {} \;