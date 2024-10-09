import argparse
import base64
import io
import logging
import os
from typing import Dict, Union

import torch
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
from kserve import InferRequest, InferResponse, Model, ModelServer, model_server
from kserve.errors import InvalidInput

logger = logging.getLogger(__name__)

class DiffusersModel(Model):
    def __init__(self, name: str):
        super().__init__(name)
        print('SG:: In __init__')

        tmp_model_id = os.environ.get('model_id')
        tmp_model_location = os.environ.get('model_location')
        tmp_model_lora_weights_location = os.environ.get('model_lora_weights_location')
        print(f'SG:: tmp_model_id={tmp_model_id}, tmp_model_location={tmp_model_location}, tmp_model_lora_weights_location={tmp_model_lora_weights_location}')

        self.model_id = args.model_id or tmp_model_id or "/mnt/models"
        self.lora_dir = args.lora_dir or tmp_model_lora_weights_location or None
        self.pipeline = None
        self.ready = False
        self.load()

    def load(self):

        # Load the model
        print(f'SG:: Loading model using from_pretrained. Model={self.model_id}')
        self.pipeline = StableDiffusionXLPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16,
            variant="fp16",
            safety_checker=None,
            use_safetensors=True,
        )

        if args.device:
            print(f"SG:: Loading model on device: {args.device}")
            if args.device == "cuda":
                self.pipeline.to(torch.device("cuda"))
            elif args.device == "cpu":
                self.pipeline.to(torch.device("cpu"))
            elif args.device == "enable_model_cpu_offload":
                self.pipeline.enable_model_cpu_offload()
            elif args.device == "enable_sequential_cpu_offload":
                self.pipeline.enable_sequential_cpu_offload()
            else:
                raise ValueError(f"Invalid device: {args.device}")
        else:
            print('SG:: Loading model on "CUDA" device')
            self.pipeline.to(torch.device("cuda"))

        logger.info('SG:: Checking if logging works or not - trying to load LoRA weights...')
        if self.lora_dir:
            print(f"SG:: Loading LoRA weights for this model from {self.lora_dir}")
            self.pipeline.load_lora_weights(self.lora_dir)
            print(f"SG:: Loaded LoRA weights for this model from {self.lora_dir}")

        # The ready flag is used by model ready endpoint for readiness probes,
        # set to True when model is loaded successfully without exceptions.
        self.ready = True

    def preprocess(
        self, payload: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Dict:
        print('SG:: preprocess...')
        if isinstance(payload, Dict) and "instances" in payload:
            print('SG:: preprocess:: setting request-type to "v1"...')
            headers["request-type"] = "v1"
        elif isinstance(payload, InferRequest):
            raise InvalidInput("v2 protocol not implemented")
        else:
            raise InvalidInput("invalid payload")

        return payload["instances"][0]

    def convert_lists_to_tuples(self, data):
        print('SG:: convert_lists_to_tuples...')
        if isinstance(data, dict):
            return {k: self.convert_lists_to_tuples(v) for k, v in data.items()}
        elif isinstance(data, list):
            return tuple(self.convert_lists_to_tuples(v) for v in data)
        else:
            return data

    def predict(
        self, payload: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Union[Dict, InferResponse]:
        print('SG:: predict...')
        payload = self.convert_lists_to_tuples(payload)

        # Create the image, without refiner if not needed
        image = self.pipeline(**payload).images[0]
        
        # Convert the image to base64
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        im_b64 = base64.b64encode(image_bytes.getvalue()).decode("utf-8")

        return {
            "predictions": [
                {
                    "model_name": self.model_id,
                    "prompt": payload["prompt"],
                    "image": {"format": "PNG", "b64": im_b64},
                }
            ]
        }


parser = argparse.ArgumentParser(parents=[model_server.parser])
parser.add_argument(
    "--model_id",
    type=str,
    help="Model ID to load (default: /mnt/models, adapt if you use the refiner model)",
)
parser.add_argument(
    "--lora_dir",
    type=str,
    help="LoRA weights will be loaded from this directory (no default value)",
)
parser.add_argument(
    "--device",
    type=str,
    help="Device to use, including offloading. Valid values are: 'cuda' (default), 'enable_model_cpu_offload', 'enable_sequential_cpu_offload', 'cpu' (works but unusable...)",
)
args, _ = parser.parse_known_args()

if __name__ == "__main__":
    print('SG:: Creating an instance of DiffusersModel...')
    model = DiffusersModel(args.model_name)
    # model.load()      # model is loaded from init

    print('SG:: Calling start() on ModelServer...')
    ModelServer().start([model])
