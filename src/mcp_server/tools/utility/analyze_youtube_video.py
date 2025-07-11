"""Analyze YouTube video using Gemini API to extract scenes for generative AI video creation."""

import os
import re
from typing import Dict, List, Optional
from google import genai
from ...utils.error_helpers import create_error_response, ErrorType


async def analyze_youtube_video(
    youtube_url: str,
    project_id: Optional[str] = None
) -> Dict:
    """
    Analyze a YouTube video to extract scenes and create a script for generative AI video creation.
    
    Args:
        youtube_url: YouTube video URL (must be public)
        project_id: Optional project to associate the analysis with
        
    Returns:
        Analysis results with scene breakdown and AI prompts
    """
    try:
        # Validate YouTube URL
        youtube_pattern = r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|^https?://youtu\.be/[\w-]+'
        if not re.match(youtube_pattern, youtube_url):
            return create_error_response(
                ErrorType.VALIDATION_ERROR,
                "Invalid YouTube URL format",
                suggestion="Use a valid YouTube URL like https://youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID"
            )
            
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return create_error_response(
                ErrorType.AUTHENTICATION,
                "GEMINI_API_KEY not found in environment variables",
                suggestion="Set the GEMINI_API_KEY environment variable with your Gemini API key"
            )
            
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Create the prompt for scene extraction
        prompt = """Analyze this video and extract a detailed scene-by-scene breakdown for recreating it using generative AI tools.

For each scene, provide:
1. Timestamp (start and end time)
2. Visual description (what's shown on screen)
3. AI image prompt (descriptive but simple prompt for text-to-image generation)
4. Motion description (for image-to-video generation)
5. Audio/narration transcript (what's being said)
6. Background music description (if any)

Format the output as a structured JSON with the following schema:
{
  "title": "Video title",
  "duration": "Total duration",
  "summary": "Brief summary of the video content",
  "scenes": [
    {
      "scene_number": 1,
      "timestamp_start": "00:00",
      "timestamp_end": "00:05",
      "visual_description": "Description of what's shown",
      "ai_image_prompt": "Simple, descriptive prompt for image generation",
      "motion_prompt": "Description of motion/animation for the scene",
      "narration": "Transcript of what's being said",
      "music_description": "Background music style/mood"
    }
  ],
  "overall_style": "Visual style consistency notes",
  "key_messages": ["Main points conveyed in the video"]
}

Focus on creating prompts that will help recreate the video's structure and message using AI tools."""

        # Generate content using Gemini
        response = client.models.generate_content(
            model='models/gemini-2.5-pro',
            contents=genai.types.Content(
                parts=[
                    genai.types.Part(
                        file_data=genai.types.FileData(file_uri=youtube_url)
                    ),
                    genai.types.Part(text=prompt)
                ]
            )
        )
        
        # Extract the text response
        result_text = response.text
        
        # Try to parse JSON from the response
        try:
            # Find JSON content in the response
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                import json
                scene_data = json.loads(json_match.group())
            else:
                # If no JSON found, return the raw text with structure
                scene_data = {
                    "raw_analysis": result_text,
                    "error": "Could not parse structured JSON from response"
                }
        except Exception as parse_error:
            scene_data = {
                "raw_analysis": result_text,
                "parse_error": str(parse_error)
            }
        
        # Prepare the response
        analysis_result = {
            "success": True,
            "youtube_url": youtube_url,
            "analysis": scene_data
        }
        
        # If project_id provided, add it to the result
        if project_id:
            analysis_result["project_id"] = project_id
            
        return analysis_result
        
    except Exception as e:
        return create_error_response(
            ErrorType.API_ERROR,
            f"Failed to analyze YouTube video: {str(e)}",
            details={"error": str(e), "url": youtube_url}
        )