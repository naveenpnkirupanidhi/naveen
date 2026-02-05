"""
Image Agent Module
Text-to-image generation using OpenAI's DALL-E API with prompt engineering.
"""

from openai import OpenAI
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class ImageAgent:
    """
    Agent for generating images from text descriptions using DALL-E.
    Includes prompt engineering to enhance image quality.
    """

    def __init__(self, api_key: str, output_dir: str = "generated_images"):
        """
        Initialize the Image Agent.

        Args:
            api_key: OpenAI API key
            output_dir: Directory to save generated images
        """
        self.api_key = api_key
        self.output_dir = output_dir
        self.client = OpenAI(api_key=api_key)

        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def enhance_prompt(self, user_prompt: str, style: str = None) -> str:
        """
        Enhance the user's prompt with additional details for better image quality.

        Args:
            user_prompt: Original user prompt
            style: Optional style preference (e.g., "realistic", "artistic", "cartoon")

        Returns:
            Enhanced prompt string
        """
        # Use GPT to enhance the prompt
        try:
            style_guidance = ""
            if style:
                style_guidance = f" The image should be in a {style} style."

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at writing prompts for AI image generation.
Your task is to enhance user prompts to create better, more detailed image descriptions.

Guidelines:
- Add specific visual details (lighting, composition, colors)
- Include artistic style elements if appropriate
- Keep the core concept from the user's prompt
- Add descriptive adjectives that enhance visual quality
- Keep the enhanced prompt under 200 words
- DO NOT include any harmful, violent, or inappropriate content
- Return ONLY the enhanced prompt, no explanations"""
                    },
                    {
                        "role": "user",
                        "content": f"Enhance this image prompt: {user_prompt}{style_guidance}"
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )

            enhanced = response.choices[0].message.content.strip()
            return enhanced

        except Exception as e:
            # If enhancement fails, return original prompt
            print(f"Prompt enhancement error: {str(e)}")
            return user_prompt

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        enhance: bool = True,
        style: str = None
    ) -> dict:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the desired image
            size: Image size ("1024x1024", "1792x1024", or "1024x1792")
            quality: Image quality ("standard" or "hd")
            enhance: Whether to enhance the prompt
            style: Style preference for prompt enhancement

        Returns:
            Dictionary with image URL, path, and metadata
        """
        result = {
            'original_prompt': prompt,
            'enhanced_prompt': None,
            'image_url': None,
            'local_path': None,
            'size': size,
            'quality': quality,
            'error': None
        }

        try:
            # Enhance prompt if requested
            if enhance:
                enhanced_prompt = self.enhance_prompt(prompt, style)
                result['enhanced_prompt'] = enhanced_prompt
                final_prompt = enhanced_prompt
            else:
                final_prompt = prompt

            # Generate image using DALL-E 3
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                size=size,
                quality=quality,
                n=1
            )

            # Get the image URL
            image_url = response.data[0].url
            result['image_url'] = image_url

            # Optionally save the image locally
            if image_url:
                local_path = self._save_image(image_url, prompt)
                result['local_path'] = local_path

        except Exception as e:
            error_msg = str(e)
            if "invalid_request" in error_msg.lower():
                result['error'] = f"Invalid request: {error_msg}"
            elif "rate_limit" in error_msg.lower():
                result['error'] = "Rate limit exceeded. Please try again later."
            elif "authentication" in error_msg.lower():
                result['error'] = "Authentication failed. Check your API key."
            else:
                result['error'] = f"Image generation error: {error_msg}"

        return result

    def _save_image(self, url: str, prompt: str) -> Optional[str]:
        """
        Download and save an image locally.

        Args:
            url: Image URL
            prompt: Original prompt (used for filename)

        Returns:
            Local file path or None if failed
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Create filename from timestamp and sanitized prompt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in " -_").strip()
            safe_prompt = safe_prompt.replace(" ", "_")
            filename = f"{timestamp}_{safe_prompt}.png"

            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return filepath

        except Exception as e:
            print(f"Error saving image: {str(e)}")
            return None

    def get_style_options(self) -> Dict[str, str]:
        """
        Get available style options for image generation.

        Returns:
            Dictionary of style names and descriptions
        """
        return {
            "realistic": "Photorealistic style with natural lighting",
            "artistic": "Artistic interpretation with creative elements",
            "cartoon": "Cartoon or animated style",
            "oil_painting": "Classical oil painting style",
            "watercolor": "Soft watercolor painting style",
            "digital_art": "Modern digital art style",
            "sketch": "Pencil sketch or line drawing style",
            "3d_render": "3D rendered image style",
            "minimalist": "Clean, minimalist design",
            "vintage": "Retro or vintage aesthetic"
        }

    def query(self, question: str) -> dict:
        """
        Process an image generation request.

        Args:
            question: User's image request

        Returns:
            Dictionary with generation results
        """
        result = {
            'prompt': question,
            'image_url': None,
            'local_path': None,
            'enhanced_prompt': None,
            'formatted': '',
            'error': None
        }

        # Check if user specified a style
        style = None
        question_lower = question.lower()
        styles = self.get_style_options()

        for style_name in styles.keys():
            if style_name.replace("_", " ") in question_lower:
                style = style_name
                break

        # Extract the core prompt (remove common request words)
        prompt = question
        remove_phrases = [
            'generate an image of',
            'generate image of',
            'create an image of',
            'create image of',
            'draw',
            'make an image of',
            'make image of',
            'i want an image of',
            'show me',
            'picture of',
            'image of'
        ]

        prompt_lower = prompt.lower()
        for phrase in remove_phrases:
            if phrase in prompt_lower:
                idx = prompt_lower.index(phrase)
                prompt = prompt[idx + len(phrase):].strip()
                break

        # Generate the image
        gen_result = self.generate_image(prompt, style=style)

        result['image_url'] = gen_result.get('image_url')
        result['local_path'] = gen_result.get('local_path')
        result['enhanced_prompt'] = gen_result.get('enhanced_prompt')
        result['error'] = gen_result.get('error')

        # Format output
        if result['error']:
            result['formatted'] = f"Image Generation Error: {result['error']}"
        else:
            lines = []
            lines.append("Image Generated Successfully!")
            lines.append("-" * 40)
            lines.append(f"Original Prompt: {question}")
            if result['enhanced_prompt']:
                lines.append(f"\nEnhanced Prompt: {result['enhanced_prompt']}")
            if result['image_url']:
                lines.append(f"\nImage URL: {result['image_url']}")
            if result['local_path']:
                lines.append(f"Saved to: {result['local_path']}")
            result['formatted'] = "\n".join(lines)

        return result


# Test the Image Agent
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from config import OPENAI_API_KEY

    agent = ImageAgent(OPENAI_API_KEY)

    print("Testing Image Agent")
    print("=" * 60)

    # Test prompt enhancement
    test_prompt = "a cat sitting on a windowsill"
    print(f"Original prompt: {test_prompt}")

    enhanced = agent.enhance_prompt(test_prompt, "artistic")
    print(f"Enhanced prompt: {enhanced}")

    # Note: Actual image generation will incur API costs
    print("\nTo generate an image, use:")
    print('agent.generate_image("your prompt here")')
