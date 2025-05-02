"""
Unit tests for SSIM validation in video frames.
"""

import os
import unittest
from lib.video.validation.ssim_validation import ssim_validation, ssim_validation_dir

from lib.video.generation.generation_classes import VideoGenerationAnimateDiff


class TestSSIMValidation(unittest.TestCase):
    """
    Unit tests for SSIM validation in video frames.
    """
    def setUp(self):
        """
        Set up a temporary directory with test frames for SSIM validation.
        """
        animatediff_input = VideoGenerationAnimateDiff.AnimateDiffPipelineInput(
            num_frames=8,
            guidance_scale=7.5,
            num_inference_steps=25,
            fps=8,
        )

        self.test_dir = "TestSSIMValidation"
        os.mkdir(self.test_dir)

        self.generator = VideoGenerationAnimateDiff(animatediff_input)
        self.generator.allocate_resources()

        prompt = "cinematic animation in ultra-high detail, soft lighting, dynamic range, shallow depth of field, expressive character motion, realistic textures, golden hour glow, slow camera pan, natural background, 4k film style, "
        negative_prompt = "deformed, blurry, mutated, extra limbs, extra fingers, bad hands, low quality, distorted face, missing limbs, broken anatomy, fuzzy, dark, messy background, ugly, glitch, horror style, static pose, photorealistic, grayscale,"

        self.generator.set_prompt(prompt)
        self.generator.set_negative_prompt(negative_prompt)

        self.generator.generate()
        self.generator.export_to_png(f"{self.test_dir}/test_story.png")

    def tearDown(self):
        """
        Clean up the temporary directory after the test.
        """
        self.generator.deallocate_resources()

        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)

    def test_dir_ssim_equals_pil_format(self):
        """
        Test SSIM computation for two identical frames.
        """
        _normal = ssim_validation(self.generator.videos[0])
        _dir    = ssim_validation_dir(self.test_dir)
        
        self.assertAlmostEqual(_normal, _dir, places=2)


if __name__ == "__main__":
    unittest.main()
