#!/bin/sh

REPO_ROOT_DIR=$1          # "/opt/app-root/src/demo/sgahlot-nvidia-usecase"
CODE_MAR_DIR="$REPO_ROOT_DIR/code/mar"
SAVED_MODEL_DIR="$REPO_ROOT_DIR/models/tuned-toy-jensen/model"
MODEL_ZIP_FILE_NAME="model.zip"
MAR_MODEL_NAME="stable-diffusion"

printf "REPO_ROOT_DIR=%s\n" $REPO_ROOT_DIR

cd $SAVED_MODEL_DIR
mkdir -p ../gen-mar/archive/config
mkdir ../gen-mar/archive/model-store

# Create zip file containing the model directory
printf "In the SAVED_MODEL_DIR - PWD=%s. Creating [%s] in (gen-mar dir) containing model dir\n" `pwd` $MODEL_ZIP_FILE_NAME
zip -r ../gen-mar/$MODEL_ZIP_FILE_NAME *
cd ../gen-mar

printf "Copying config.properties, requirements.txt and stable_diffusion_handler...\n"
cp ${CODE_MAR_DIR}/config.properties archive/config
cp ${CODE_MAR_DIR}/requirements.txt .
cp ${CODE_MAR_DIR}/stable_diffusion_handler .

# Install and run torch-model-archiver
printf "Installing torch-model-archiver"
pip install -q torch-model-archiver

torch-model-archiver --model-name $MAR_MODEL_NAME \
    --version 1.0 \
    --handler ./stable_diffusion_handler.py \
    --extra-files ./$MODEL_ZIP_FILE_NAME \
    -f -r requirements.txt

mv ${MAR_MODEL_NAME}.mar archive/model-store

printf "In the gen-mar dir - PWD=%s. Files after running archiver:\n" `pwd`
find archive -type f -exec ls -lh {} \;

pip uninstall -y -q torch-model-archiver
