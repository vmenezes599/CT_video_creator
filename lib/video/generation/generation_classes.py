"""
Prototype for video generation using Stable Diffusion and AnimateDiff
"""

from typing import List

import PIL.Image
import torch
from diffusers import AnimateDiffPipeline, DDIMScheduler, MotionAdapter
from diffusers.utils import export_to_gif, export_to_video
from .environment_variables import EnvironmentVariables


class VideoGenerationBase:
    """
    Base class for video generation classes with helper functions.
    """

    def __init__(self):
        self.pipe = None
        self.videos : List[List[PIL.Image.Image]] = None
    
    def inspect_tokens(self, prompt: str):
        """
        Inspects the tokens and token count for a given prompt.
        """
        if not self.pipe or not hasattr(self.pipe, "tokenizer"):
            raise RuntimeError("Pipeline or tokenizer is not initialized. Call allocate_resources() first.")

        # Tokenize the prompt
        tokens = self.pipe.tokenizer(prompt, return_tensors="pt", truncation=True)

        # Get token IDs and decode them
        token_ids = tokens["input_ids"][0].tolist()
        decoded_tokens = [self.pipe.tokenizer.decode([token_id]) for token_id in token_ids]

        # Print token information
        print(f"Prompt: {prompt}")
        print(f"Number of tokens: {len(token_ids)}")
        print(f"Tokens: {decoded_tokens}")
        
    def export_to_png(self, filename):
        """
        Exports the generated frames to a PNG file.
        """
        if self.videos is None:
            raise ValueError("No frames to export. Please generate frames first.")
        
        for video in self.videos:
            for i, frame in enumerate(video):
                if "." in filename:
                    name, ext = filename.rsplit(".", 1)
                    processed_file_name = f"{name}_b{i}.{ext}"
                else:
                    processed_file_name = f"{filename}_b{i}.png"

                frame.save(processed_file_name)
                print(f"Exported {processed_file_name}")

    def export_to_gif(self, filename):
        """
        Exports the generated frames to a GIF file.
        """
        for i, video in enumerate(self.videos):
            if "." in filename:
                name, ext = filename.rsplit(".", 1)
                processed_file_name = f"{name}_b{i}.{ext}"
            else:
                processed_file_name = f"{filename}_b{i}.gif"
            export_to_gif(video, processed_file_name)
            print(f"Exported {processed_file_name}")

    def export_to_video_custom_fps(self, filename: str, fps: int = 8):
        """
        Exports the generated frames to a video file.
        """

        for i, video in enumerate(self.videos):
            if "." in filename:
                name, ext = filename.rsplit(".", 1)
                processed_file_name = f"{name}_b{i}.{ext}"
            else:
                processed_file_name = f"{filename}_b{i}.mp4"

            export_to_video(video, processed_file_name, fps=fps)
            print(f"Exported {processed_file_name}")


class VideoGenerationAnimateDiff(VideoGenerationBase):
    """
    This class is used to generate images using the AnimateDiff model.
    """

    class AnimateDiffPipelineInput:
        """
        Configuration for the AnimateDiff pipeline.
        Allows initialization with different values for each run.
        """

        def __init__(
            self,
            num_frames: int = 16,
            guidance_scale: float = 7.5,
            num_inference_steps: int = 25,
            fps: int = 8,
            torch_dtype: torch.dtype = torch.float16,
        ):
            self.num_frames = num_frames
            self.guidance_scale = guidance_scale
            self.num_inference_steps = num_inference_steps
            self.fps = fps
            self.torch_dtype = torch_dtype

    class MotionAdapterInput:
        """
        Configuration for the motion adapter.
        Allows initialization with different values for each run.
        """

        def __init__(
            self,
            animatediff_pipeline_input: "VideoGenerationAnimateDiff.AnimateDiffPipelineInput",
            block_out_channels: list = (320, 640, 1280, 1280),  # Not used
            motion_layers_per_block: int = 2,  # Not used
            motion_transformer_layers_per_block: int = 1,  # Not used
            motion_mid_block_layers_per_block: int = 1,  # Not used
            motion_transformer_layers_per_mid_block: int = 1,  # Not used
            motion_num_attention_heads: int = 8,  # Not used
            motion_norm_num_groups: int = 32,
            motion_max_seq_length: int = 32,
            use_motion_mid_block: bool = True,  # Not used
        ):
            """
            Initializes the MotionAdapterInput with default or custom values.

            Args:
                block_out_channels (defaults to `(320, 640, 1280, 1280)`):
                    The tuple of output channels for each UNet block.
                motion_layers_per_block (`int` defaults to 2):
                    The number of motion layers per UNet block.
                motion_transformer_layers_per_block (`int`, defaults to 1):
                    The number of transformer layers to use in each motion layer in each block.
                motion_mid_block_layers_per_block (`int`, defaults to 1):
                    The number of motion layers in the middle UNet block.
                motion_transformer_layers_per_mid_block (`int` defaults to 1):
                    The number of transformer layers to use in each motion layer in the middle block.
                motion_num_attention_heads (`int`, defaults to 8):
                    The number of heads to use in each attention layer of the motion module.
                motion_norm_num_groups (`int`, defaults to 32):
                    The number of groups to use in each group normalization layer of the motion module.
                motion_max_seq_length (`int`, defaults to 32):
                    The maximum sequence length to use in the motion module.
                use_motion_mid_block (`bool`, defaults to True):
                    Whether to use a motion module in the middle of the UNet.
                conv_in_channels (`int`, defaults to None):
                    The number of input channels for the convolutional layer.
            """
            self.block_out_channels = block_out_channels
            self.motion_layers_per_block = motion_layers_per_block
            self.motion_transformer_layers_per_block = (
                motion_transformer_layers_per_block
            )
            self.motion_mid_block_layers_per_block = motion_mid_block_layers_per_block
            self.motion_transformer_layers_per_mid_block = (
                motion_transformer_layers_per_mid_block
            )
            self.motion_num_attention_heads = motion_num_attention_heads
            self.motion_max_seq_length = max(
                8, min(32, animatediff_pipeline_input.num_frames, motion_max_seq_length)
            )
            self.motion_norm_num_groups = motion_norm_num_groups
            self.use_motion_mid_block = use_motion_mid_block

    def __init__(
        self,
        animatediff_pipeline_input: AnimateDiffPipelineInput,
        motionadapter_input: MotionAdapterInput = None,
    ):
        super().__init__()

        self.animatediff_pipeline_input = animatediff_pipeline_input
        if motionadapter_input is None:
            self.motionadapter_input = self.MotionAdapterInput(
                animatediff_pipeline_input=animatediff_pipeline_input
            )
        else:
            self.motionadapter_input = motionadapter_input

        if (
            self.animatediff_pipeline_input.num_frames
            > self.motionadapter_input.motion_max_seq_length
        ):
            print(
                f"Error: Limiting num_frames ({self.animatediff_pipeline_input.num_frames}) to motion_max_seq_length ({self.motionadapter_input.motion_max_seq_length})"
            )
            self.animatediff_pipeline_input.num_frames = (
                self.motionadapter_input.motion_max_seq_length
            )

        # Below variables will be initialized afterwards when necessary
        self.model_id = None
        self.motion_model_id = None
        self.adapter = None
        self.scheduler = None
        self.prompt = None
        self.negative_prompt = None
        self.resources_alocated = False

    def allocate_resources(self):
        """
        Allocates memory by initializing the pipeline and its components.
        """
        if self.resources_alocated:
            return

        model_id = EnvironmentVariables.MODEL_NAMES[1]
        motion_model_id = EnvironmentVariables.MOTION_MODEL_NAMES[1]

        self.adapter = MotionAdapter.from_pretrained(
            motion_model_id,
            torch_dtype=self.animatediff_pipeline_input.torch_dtype,
        )

        self.pipe = AnimateDiffPipeline.from_pretrained(
            model_id,
            motion_adapter=self.adapter,
            torch_dtype=self.animatediff_pipeline_input.torch_dtype,
        )
        self.scheduler = DDIMScheduler.from_pretrained(
            model_id,
            subfolder="scheduler",
            clip_sample=False,
            timestep_spacing="linspace",
            beta_schedule="linear",
            steps_offset=1,
        )
        self.pipe.scheduler = self.scheduler

        self.pipe.enable_vae_slicing()
        self.pipe.enable_model_cpu_offload()

        self.resources_alocated = True

    def _run_pipeline(self):
        """
        Runs the pipeline to generate frames.
        """
        if not self.pipe:
            raise RuntimeError(
                "Pipeline is not initialized. Call allocate_resources() first."
            )
        generator = torch.Generator("cpu")

        print(
            f"\n generator: {generator.seed()} | num_frames: {self.animatediff_pipeline_input.num_frames} | motion_max_seq_length: {self.motionadapter_input.motion_max_seq_length} \n"
        )

        output = self.pipe(
            prompt=self.prompt,
            negative_prompt=self.negative_prompt,
            num_frames=self.animatediff_pipeline_input.num_frames,
            guidance_scale=self.animatediff_pipeline_input.guidance_scale,
            num_inference_steps=self.animatediff_pipeline_input.num_inference_steps,
            generator=generator,
        )
        self.videos = output.frames

    def deallocate_resources(self):
        """
        Deallocates memory by deleting the pipeline and its components.
        """
        if not self.resources_alocated:
            return

        del self.pipe
        del self.adapter
        del self.scheduler
        torch.cuda.empty_cache()  # Clear GPU memory if applicable

        self.resources_alocated = False

    def export_to_video(self, filename):
        """
        Exports the generated frames to a video file with the specified filename.
        """
        super().export_to_video_custom_fps(
            filename, self.animatediff_pipeline_input.fps
        )

    def set_prompt(self, prompt):
        """
        Sets the prompt for the pipeline.
        """
        self.prompt = prompt

    def set_negative_prompt(self, negative_prompt):
        """
        Sets the negative prompt for the pipeline.
        """
        self.negative_prompt = negative_prompt

    def generate(self):
        """
        Allocates resources, runs the pipeline, and deallocates resources.
        """
        if not self.resources_alocated:
            print("Resources not allocated.")
            return

        self._run_pipeline()