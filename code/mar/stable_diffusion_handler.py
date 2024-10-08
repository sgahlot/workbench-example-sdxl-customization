import logging
import zipfile
import json
from abc import ABC

import diffusers
import numpy as np
import torch
from diffusers import StableDiffusionXLPipeline

from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)
logger.info("Diffusers version %s", diffusers.__version__)


class DiffusersHandler(BaseHandler, ABC):
    """
    Diffusers handler class for text to image generation.
    """

    def __init__(self):
        self.initialized = False

    def initialize(self, ctx):
        """In this initialize function, the Stable Diffusion model is loaded and
        initialized here.
        Args:
            ctx (context): It is a JSON Object containing information
            pertaining to the model artifacts parameters.
        """
        self.manifest = ctx.manifest
        properties = ctx.system_properties
        logger.info("SG:: Reading 'model_dir' property...")
        model_dir = properties.get("model_dir")
        logger.info(f"SG:: 'model_dir'=[{model_dir}]...")
        model_store_dir = properties.get("model-store")
        logger.info(f"SG:: 'model_store_dir'=[{model_store_dir}]...")
        saved_model_store_dir = properties.get("SAVED_MODELS_DIR")
        logger.info(f"SG:: 'saved_model_store_dir'=[{model_store_dir}]...")

        self.device = torch.device(
            "cuda:" + str(properties.get("gpu_id"))
            if torch.cuda.is_available() and properties.get("gpu_id") is not None
            else "cpu"
        )
        # Loading the model and tokenizer from checkpoint and config files based on the user's choice of mode
        # further setup config can be added.
        with zipfile.ZipFile(model_dir + "/model.zip", "r") as zip_ref:
            zip_ref.extractall(model_dir + "/model")

        # logger.info(f"SG:: Trying to load model from [{model_dir}/model] directory...")
        # self.pipe = StableDiffusionXLPipeline.from_pretrained(model_dir + "/model")

        model_id="stabilityai/stable-diffusion-xl-base-1.0"

        logger.info(f"SG:: Using [{model_id}] as the pre-trained model for this demo")
        self.pipe = StableDiffusionXLPipeline.from_pretrained(model_id, torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
        self.pipe.to(self.device)
        logger.info(f"SG:: Loaded [{model_id}] for this demo")

        logger.info(f"SG:: Loading LoRA weights for this model")
        # TODO(SG): Uncomment to load LoRA weights once it's available and the model loads successfully 
        self.pipe.load_lora_weights(model_dir + "/model")
        logger.info(f"SG:: Loaded LoRA weights for this model")

        self.initialized = True

    def preprocess(self, requests):
        """Basic text preprocessing, of the user's prompt.
        Args:
            requests (str): The Input data in the form of text is passed on to the preprocess
            function.
        Returns:
            list : The preprocess function returns a list of prompts.
        """
        inputs = []

        for _, data in enumerate(requests):
            input_text = data['body']['instances'][0]['data']
            if input_text is None:
                input_text = data.get("body")
            if isinstance(input_text, (bytes, bytearray)):
                input_text = input_text.decode("utf-8")
            logger.info("Received text: '%s'", input_text)
            inputs.append(input_text)
        return inputs

    def inference(self, inputs):
        """Generates the image relevant to the received text.
        Args:
            input_batch (list): List of Text from the pre-process function is passed here
        Returns:
            list : It returns a list of the generate images for the input text
        """
        # Handling inference for sequence_classification.
        inferences = self.pipe(
            inputs, guidance_scale=7.5, num_inference_steps=50, height=768, width=768
        ).images

        logger.info("Generated image: '%s'", inferences)
        return inferences

    def postprocess(self, inference_output):
        """Post Process Function converts the generated image into Torchserve readable format.
        Args:
            inference_output (list): It contains the generated image of the input text.
        Returns:
            (list): Returns a list of the images.
        """
        images = []
        logger.info("::inference_output:: %s", inference_output)
        for image in inference_output:
            logger.info("::array:: %s", np.array(image).tolist())
            images.append(np.array(image).tolist())
        return images