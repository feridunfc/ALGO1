# module_2_diffusion_generator.py
# pip install diffusers torch Pillow

import torch
from diffusers import DDPMPipeline
from PIL import Image
import numpy as np

class SyntheticMarketDataGenerator:
    """Uses a diffusion model to generate synthetic 'image-like' market data."""
    def __init__(self, pretrained_model_name="google/ddpm-cat-256"):
        self.pipeline = DDPMPipeline.from_pretrained(pretrained_model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline.to(self.device)
        print("Diffusion pipeline loaded.")

    def generate(self, num_samples=1, seed=None):
        generator = torch.Generator(device=self.device)
        if seed is not None:
            generator.manual_seed(seed)
        images = self.pipeline(batch_size=num_samples, generator=generator).images
        print(f"Generated {len(images)} synthetic data samples.")
        return images

if __name__ == "__main__":
    gen = SyntheticMarketDataGenerator()
    synthetic_images = gen.generate(num_samples=1, seed=42)
    image = synthetic_images[0]
    image.save("synthetic_correlation_matrix.png")
    arr = np.array(image)
    print("Saved 'synthetic_correlation_matrix.png' with shape:", arr.shape)
