"""Analyze YouTube video using Gemini API to extract scenes for generative AI video creation."""

import os
import re
import json
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
            
        # Get API key from environment - try both GEMINI_API_KEY and GOOGLE_API_KEY
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return create_error_response(
                ErrorType.AUTHENTICATION,
                "GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables",
                suggestion="Set either GEMINI_API_KEY or GOOGLE_API_KEY environment variable with your Google AI API key"
            )
            
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Create the comprehensive prompt for scene extraction with all requirements
        prompt = """Analyze this video comprehensively and extract a detailed scene-by-scene breakdown for recreating it using generative AI tools.

IMPORTANT REQUIREMENTS:
1. Extract ALL narration/voiceover content VERBATIM (word-for-word exactly as spoken)
2. Identify and categorize ALL visual themes and patterns
3. Note ALL transitions between scenes and their types (cut, fade, dissolve, wipe, etc.)
4. Analyze the pacing and production quality
5. Identify recurring visual motifs or stylistic elements

For each scene, provide:
1. Scene number and timestamp (start and end time in MM:SS format)
2. Visual description (detailed description of what's shown on screen)
3. AI image prompt (descriptive but simple prompt for text-to-image generation)
4. Motion description (camera movements, object motion, animation for image-to-video)
5. Narration/voiceover (EXACT verbatim transcript of what's being said)
6. Background music description (style, mood, instruments if any)
7. Transition to next scene (type and duration)

Format the output as a structured JSON with the following schema:
{
  "title": "Video title",
  "duration": "Total duration in MM:SS format",
  "total_scenes": <number of scenes>,
  "summary": "Brief summary of the video content and purpose",
  "scenes": [
    {
      "scene_number": 1,
      "timestamp_start": "00:00",
      "timestamp_end": "00:05",
      "visual_description": "Detailed description of visuals",
      "ai_image_prompt": "Simple, descriptive prompt for image generation",
      "motion_prompt": "Camera movements and object motion description",
      "narration_verbatim": "EXACT word-for-word transcript or null if no speech",
      "music_description": "Background music style/mood or null if none",
      "transition_to_next": {
        "type": "cut|fade|dissolve|wipe|other",
        "duration_ms": 500,
        "description": "Transition details"
      }
    }
  ],
  "visual_themes": {
    "primary_theme": "Main visual style or theme",
    "color_palette": ["dominant colors"],
    "style_elements": ["visual style characteristics"],
    "recurring_motifs": ["patterns or elements that repeat"]
  },
  "pacing_analysis": {
    "average_scene_duration": "Average duration in seconds",
    "tempo": "slow|moderate|fast|variable",
    "scenes_per_minute": <number>,
    "rhythm_pattern": "Description of pacing pattern"
  },
  "production_quality": {
    "overall_quality": "low|medium|high|professional",
    "visual_quality": "Description of visual production quality",
    "audio_quality": "Description of audio production quality",
    "editing_style": "Description of editing approach",
    "notable_techniques": ["Special techniques or effects used"]
  },
  "audio_analysis": {
    "has_narration": true|false,
    "narration_style": "conversational|formal|educational|promotional|etc",
    "music_presence": "none|background|prominent",
    "sound_effects": ["list of notable sound effects"]
  },
  "key_messages": ["Main points or messages conveyed"],
  "target_audience": "Intended audience description",
  "call_to_action": "Any CTA present in the video or null"
}

CRITICAL: Ensure ALL narration is captured VERBATIM - every word exactly as spoken.
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
        
        # Try to parse JSON from the response with improved handling
        try:
            # First try to find JSON in markdown code blocks
            json_in_markdown = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', result_text)
            if json_in_markdown:
                scene_data = json.loads(json_in_markdown.group(1))
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    scene_data = json.loads(json_match.group())
                else:
                    # If no JSON found, return the raw text with structure
                    scene_data = {
                        "raw_analysis": result_text,
                        "error": "Could not parse structured JSON from response",
                        "suggestion": "The analysis was completed but returned in an unexpected format"
                    }
        except json.JSONDecodeError as e:
            # Provide more detailed error information
            scene_data = {
                "raw_analysis": result_text,
                "parse_error": str(e),
                "error_position": e.pos if hasattr(e, 'pos') else None,
                "suggestion": "JSON parsing failed - check raw_analysis for the complete response"
            }
        except Exception as parse_error:
            scene_data = {
                "raw_analysis": result_text,
                "parse_error": str(parse_error),
                "error_type": type(parse_error).__name__
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