# Stable Diffusion XL in Red Hat OpenShift AI

This readme shows how to fine-tune a [Stable Diffusion XL model](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) in [Red Hat OpenShift AI (RHOAI)](https://www.redhat.com/en/technologies/cloud-computing/openshift/openshift-ai) along with the steps to fine-tune the model. 

This project takes the latest SDXL model and familiarizes it with Toy Jensen via finetuning on a few pictures, thereby teaching it to generate new images which include him when it didn't recognize him previously.

Once the model is fine-tuned we will show the steps to deploy the model in RHOAI as well as to access the deployed model to generate the image.


## Quickstart

Open up `Red Hat OpenShift AI` by selecting it from OpenShift Applicatin Launcher. This will open up Red Hat OpenShift AI in a new tab.

### Create Data Science project
Select Data Science Projects in the left navigation menu.

Create a new Data Science project by clicking on `Create data science project` button.
Provide the `Name` as well as the `Resource name` for the project, and click on `Create` button. This will create a new data science project for you.

Select your newly created project by clicking on it.

### Setup MinIO
This project uses `MinIO` for storing the LoRA weights generated while fine-tuning the base image.

To setup MinIO execute the following command:
```
MINIO_USER=<USERNAME> \
   MINIO_PASSWORD="<PASSWORD>" \
   envsubst < minio-setup.yml | \
   oc apply -f - -n <PROJECT_CREATED_IN_PREVIOUS_STEP>
```
* _Setup `<USERNAME>` and `<PASSWORD>` to some valid values, in the above command, before executing it_

Once MinIO is setup, you can access it within your project. The yaml that was applied above creates these two routes:
* `minio-ui` - for accessing the MinIO UI
* `minio-api` - for API access to MinIO
  * Take note of the `minio-api` route location as that will be needed in next section.

### Create workbench
To use RHOAI for this project, we need to create a workbench first. In the newly created data science project, create a new Workbench by clicking `Create workbench` button in the `Workbenches` tab.

When creating the workbench, add the following environment variables:
* AWS_ACCESS_KEY_ID
  * MinIO user name
* AWS_SECRET_ACCESS_KEY
  * MinIO password
* AWS_S3_ENDPOINT
  * This is `minio-api` route location
* AWS_S3_BUCKET
  * This bucket will be created later on and the LoRA weights will be uploaded to this bucket
* AWS_DEFAULT_REGION
  * Set it to us-east-1

  _The environment variables can be added one by one, or all together by using a secret yaml file_

Use the following values for other fields:
* _Notebook image_:
  * Image selection: **PyTorch**
  * Version selection: **2024.1**
* _Deployment size_:
  * Container size: **Medium**
  * Accelerator: **NVIDIA GPU**
  * Number of accelerators: **1**
* _Cluster storage_: **50GB**

Create the workbench with above settings.

### Open workbench
Now that the workbench is created and running, follow these steps to setup the project:
* Open the workbench by clicking on the Open link for the workbench created, in the Workbenches tab
* In the workbench, click on `Terminal` icon in the `Launcher` tab.
* Clone this repository in the `Terminal`

### Run Jupyter notebook
_The notebook mentioned in this section is used to take the base model and fine-tune it to generate LoRA weights that are used later on to generate toy-jensen image_

* Once the workbench opens up in a new tab, select the folder where you cloned the repository and navigate to `code/rhoai` directory and open up the [main Jupyter Notebook](./FineTuning-SDXL.ipynb)
* Run this notebook by selecting `Run` -> `Run All Cells` menu item
* _When the notebook successfully runs, your fine-tuned model should have been uploaded to MinIO in the bucket mentioned in `Create Workbench` section_.


### Create Data connection
Create a new data connection that can be used by the init-container (`storage-initializer`) to fetch the LoRA weights generated in next step when deploying the model.

To create a Data connection, use the following steps:
* Click on `Add data connection` button in the  `Data connections` tab in your newly created project
* Fill in all the fields for this data connection
* Create the data connection by clicking on `Add data connection` button

### Deploy model
Once the initial notebook has run successfully and the data connection is created, you can deploy the model by following these steps:
* Click on `Deploy model` button in the  `Models` tab in your newly created project
* Fill in the following fields as described below:
  * _Model name:_ **<PROVIDE_a_name_for_the_model>**
  * _Serving runtime:_ **Stable Diffusion**
  * _Model framework:_ **sdxl**
  * _Model server size:_ **Small**
  * _Accelerator:_ **NVIDIA GPU**
  * _Model location:_ Select **Existing data connection** option
    * _Name:_ **Name of data connection created in previous step**
    * _Path:_ **model**
* Click on `Deploy` to deploy this model

Copy the `infernece endpoint` once the model is deployed successfully (_it will take a few minutes to deploy the model_).

### Generate image
A toy-jensen image can now be generated, using the deployed model. To generate and retrieve the image, use the following steps:
* Open up [this Jupyter Notebook](./GenerateImageUsingModel.ipynb)
* Set the value of `inference_endpoint` variable correctly by pointing it to your model's infernece endpoint
  * _Your model `inference endpoint` should have been copied in the previous section_
* Run this notebook by selecting `Run` -> `Run All Cells` menu item
* _When the notebook successfully runs, you should see a toy-jensen image generated in the last cell_.

## System used
* Red Hat OpenShift AI: `2.10.0`
* GPU: 1x NVIDIA `A10G`
* Storage: 50GB

## Python module versions
Even though we used the latest version for all the modules we installed for this project, here are the versions that are actually used underneath (in case any version incompatibility occurs in future):

* accelerate: `1.0.1`
* dataclass_wizard: `0.23.0`
* diffusers: `0.31.0.dev0`
* ipywidgets: `8.1.2`
* jupyterlab: `3.6.7`
* huggingface_hub: `0.25.2`
* minio: `7.2.7`
* peft: `0.13.2`
* transformers: `4.45.2`
* torch: `2.2.2+cu121`
* torchvision: `0.17.2+cu121`

## More notebooks
The following notebooks contain output to give you an idea on how the outputs will look when the notebooks are run:
* [FineTuning-SDXL-01](./more_notebooks/FineTuning-SDXL-with_output.ipynb)
* [FineTuning-SDXL-02](./more_notebooks/FineTuning-SDXL-with_output-02.ipynb)
* [GenerateImageUsingModel](./more_notebooks/GenerateImageUsingModel-with_output.ipynb)
