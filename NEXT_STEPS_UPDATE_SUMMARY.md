# Next Steps Update Summary

This document summarizes the updates made to all tool "next_steps" outputs to reflect the actual workflow including queuing functionality.

## Tools Updated

### 1. **generate_video_from_image**
- Added guidance for using `return_queue_id=True` for batch processing
- Emphasized voiceover-first workflow
- Added queue status checking instructions
- Clarified that assemble_video handles all audio mixing

### 2. **generate_image_from_text**
- Added conditional project/scene IDs in animation suggestions
- Mentioned batch animations with queuing
- Suggested using generate_image_from_image for style consistency

### 3. **create_project**
- Emphasized voiceover-first workflow with analyze_script
- Added generate_speech FIRST for narrated videos
- Mentioned batch processing with return_queue_id=True
- Clarified final assembly step

### 4. **add_scene**
- Added specific duration parameter in animation example
- Mentioned batch processing workflow
- Added queue monitoring with get_queue_status

### 5. **generate_music**
- Clarified that assemble_video handles ALL audio mixing
- Removed misleading add_audio_track suggestion
- Added note about multiple music tracks

### 6. **generate_speech**
- Emphasized visual sync with narration timing
- Added batch video generation mention
- Updated duration warning options
- Clarified audio mixing is automatic

### 7. **analyze_script**
- Added project_id parameter to speech generation
- Included batch generation workflow
- Added queue monitoring step
- Emphasized timing-based scene addition

### 8. **generate_image_from_image**
- Added return_queue_id=True in animation suggestion
- Emphasized character consistency workflow
- Added batch transformation guidance
- Included queue monitoring

### 9. **download_assets**
- Added queue status checking before assembly
- Noted that queued generations auto-download
- Updated assembly guidance

### 10. **add_audio_track**
- Added strong note that this is rarely needed
- Clarified it's only for post-processing
- Emphasized using assemble_video for normal workflow

## Key Workflow Improvements

### 1. Voiceover-First Workflow
All relevant tools now emphasize generating speech FIRST for narrated videos to establish proper timing.

### 2. Queue-Based Batch Processing
Tools now consistently recommend using `return_queue_id=True` for multiple video generations and provide queue monitoring guidance.

### 3. Audio Assembly Clarification
All tools now clearly state that `assemble_video()` handles ALL audio mixing automatically, eliminating confusion about when to use `add_audio_track()`.

### 4. Character Consistency
Image generation tools now emphasize using the same reference image for all character scenes.

## CLAUDE.md Updates

Added comprehensive workflow reminders including:
- Voiceover-first workflow steps
- Queue usage best practices
- Audio assembly clarification
- Character consistency rules
- Batch processing example code

These updates ensure that the tool outputs guide users through the actual, optimal workflow for video generation with proper queuing support.