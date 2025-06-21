"""Cinematic photography guide prompt implementation."""

from pathlib import Path


async def cinematic_photography_guide() -> str:
    """Provide professional camera and cinematography guidance for enhanced visuals."""
    
    # Load the camera.md content if available
    camera_md_path = Path("/home/frade/videoagent/docs/camera.md")
    camera_knowledge = ""
    
    if camera_md_path.exists():
        try:
            with open(camera_md_path, 'r') as f:
                camera_knowledge = f.read()
        except:
            camera_knowledge = ""
    
    return f"""# 🎥 Cinematic Photography Guide for Video Creation

This guide helps you create professional, cinematic visuals using AI image and video generation tools.

## ⚠️ IMPORTANT: Camera Type Selection

### 📸 FOR STILL IMAGES (generate_image_from_text, generate_image_from_image)
Use **STILL PHOTOGRAPHY CAMERAS** and lenses:
- Canon 5D Mark IV, Nikon D850, Sony A7R IV
- Canon 85mm f/1.2L, Nikon 50mm f/1.4, Zeiss 35mm f/1.4
- Include photography terms: "shallow DOF", "bokeh", "f-stop"

### 🎬 FOR VIDEO GENERATION (generate_video_from_image)
Use **CINEMA/VIDEO CAMERAS** and cine lenses:
- ARRI Alexa, RED Dragon, Blackmagic URSA
- Zeiss Master Prime 35mm T1.3, Cooke S4/i 50mm T2.0
- Include motion terms: "dolly", "crane shot", "tracking"

## 🎬 Quick Cinematic Formulas

### Opening Shot (Establishing) - FOR VIDEO
```
"{{description}}, shot on ARRI Alexa, Zeiss Master Prime 24mm T1.3, cinematic widescreen, 
golden hour lighting, crane shot rising, professional cinematography"
```

### Character/Portrait Scenes - FOR STILLS
```
"{{description}}, Canon 85mm f/1.2L, shallow depth of field, creamy bokeh, 
shot on Canon 5D Mark IV, natural window lighting, eye-level angle"
```

### Action Sequences - FOR VIDEO
```
"{{description}}, RED Dragon 8K, Angenieux 24-290mm zoom, high frame rate,
compressed perspective, handheld documentary style, high contrast"
```

### Emotional/Intimate Moments - FOR STILLS
```
"{{description}}, Nikon 50mm f/1.2, intimate framing, soft lighting, 
shot on Nikon D850, Kodak Portra 400 film aesthetic"
```

### Closing Shot - FOR VIDEO
```
"{{description}}, ARRI Alexa LF, Panavision anamorphic lens, blue hour lighting, 
slow dolly out, cinematic color grading, wide establishing shot"
```

## 📸 Scene-Specific Recommendations

### By Scene Position
1. **Opening Scene**: Wide establishing shot, golden hour, slow reveal
2. **Middle Scenes**: Mix of wide/medium/close shots, varied angles
3. **Climax Scene**: Dynamic angles, dramatic lighting, energetic movement
4. **Closing Scene**: Wide pullback, blue hour, contemplative mood

### By Content Type
- **Product Showcase**: "100mm macro lens, studio lighting, 360-degree orbit"
- **Tutorial/Educational**: "35mm lens, natural lighting, static tripod shot"
- **Narrative/Story**: "Cinematic 2.39:1 aspect ratio, film grain, varied focal lengths"
- **Social Media**: "Vertical 9:16 framing, vibrant colors, eye-catching composition"

## 🎯 Platform-Optimized Cinematography

### YouTube (16:9)
- Use "cinematic widescreen composition"
- Mix wide establishing with medium shots
- Professional color grading

### TikTok/Reels (9:16)
- Add "vertical framing, mobile-first composition"
- Dynamic handheld movement
- High contrast, vibrant colors

### Instagram (1:1 or 4:5)
- Include "square format composition" or "portrait orientation"
- Central subject placement
- Soft, appealing lighting

## 💡 Pro Cinematography Tips

### Camera Movement Phrases
- **Building Tension**: "slow dolly in, gradually revealing"
- **Energy**: "quick whip pan, dynamic handheld tracking"
- **Smooth**: "steadicam glide, floating movement"
- **Dramatic**: "low angle crane shot, hero perspective"

### Lighting Keywords
- **Warm/Inviting**: "golden hour, warm tones, soft shadows"
- **Dramatic**: "chiaroscuro lighting, strong contrast"
- **Modern**: "clean studio lighting, even illumination"
- **Moody**: "blue hour, neon accents, atmospheric haze"

### Depth & Dimension
- **Shallow DOF**: "f/1.2 aperture, creamy bokeh, subject isolation"
- **Deep Focus**: "f/11 aperture, everything in sharp focus"
- **Layered**: "foreground, midground, background elements"

## 🔧 Technical Enhancement Words

### Add Authenticity
- "shot on [camera model]"
- "filmed with [lens model]"
- "[film stock] aesthetic"
- "professional cinematography"

### Add Style
- "cinematic color grading"
- "anamorphic lens flares"
- "film grain texture"
- "letterboxed widescreen"

### Add Movement (for video)
- "smooth tracking shot"
- "parallax movement"
- "subtle zoom progression"
- "organic handheld motion"

## 📝 Example Enhanced Prompts

### Before:
"A coffee shop interior"

### After - FOR STILL IMAGE:
"A cozy coffee shop interior, shot on Canon 5D Mark IV, Canon 35mm f/1.4L lens, 
warm window lighting, shallow depth of field, steam rising from coffee cups, 
professional photography, high resolution still"

### After - FOR VIDEO:
"A cozy coffee shop interior, shot on ARRI Alexa Mini, Zeiss Master Prime 35mm T1.3,
warm practical lighting, cinematic depth, steam rising dynamically,
smooth dolly forward revealing the space"

### Before (Motion):
"Camera moves forward"

### After - VIDEO MOTION PROMPT:
"Smooth dolly forward on Chapman PeeWee, ARRI Alexa LF with Cooke S4/i 25mm,
steadicam glide through the coffee shop, subtle parallax movement, 
gradual focus pull from cups to barista, cinematic camera movement"

## 🎨 Style Combinations

### Documentary Style - FOR VIDEO
"Handheld camera, natural lighting, raw authentic feel, Canon C300, 
Canon CN-E 24-70mm T2.8 cine zoom, observational framing, cinema verite"

### Documentary Style - FOR STILLS
"Photojournalistic approach, Nikon D6, 24-70mm f/2.8, natural lighting,
candid moments, decisive moment capture"

### Vintage Film - FOR STILLS
"Shot on Hasselblad 500CM, Kodak Portra 400, medium format, 
film grain, slightly desaturated colors, nostalgic mood"

### Modern Commercial - FOR VIDEO
"RED Komodo 6K, Zeiss CP.3 primes, crystal clear quality, 
professional lighting, product showcase, smooth camera movements"

### Modern Commercial - FOR STILLS
"Sony A7R IV, Sony 90mm f/2.8 macro, studio strobes,
product photography aesthetic, clean composition, tack sharp"

### Artistic/Experimental
"Double exposure effect, tilt-shift lens, selective focus,
light leaks, experimental framing, artistic interpretation"

## 🚀 Quick Implementation

To use these enhancements:
1. **IDENTIFY YOUR OUTPUT**: Still image or video?
2. **CHOOSE APPROPRIATE CAMERA**: 
   - Stills → Photography cameras (Canon 5D, Nikon D850, Sony A7R)
   - Video → Cinema cameras (ARRI, RED, Blackmagic)
3. **SELECT MATCHING LENSES**:
   - Stills → Photo lenses with f-stops (85mm f/1.2)
   - Video → Cine lenses with T-stops (85mm T1.3)
4. Add lighting and composition details
5. For video, include camera movement terms

## 🎨 Image Enhancement Workflow

When working with existing images, use generate_image_from_image to apply cinematic transformations:

### Example Transformations:
```
# Add cinematic lighting
generate_image_from_image("/path/to/image.jpg", "golden hour lighting, warm tones, cinematic color grading")

# Change camera perspective
generate_image_from_image(image_url, "shot with 85mm lens, shallow depth of field, bokeh background")

# Add atmosphere
generate_image_from_image(image_url, "add fog, volumetric lighting, moody atmosphere")

# Professional color grading
generate_image_from_image(image_url, "teal and orange color grading, high contrast, cinema LUT")
```

## 📋 Quick Reference

### 📸 STILL IMAGE CAMERAS & LENSES
- **Cameras**: Canon 5D Mark IV, Nikon D850, Sony A7R IV, Hasselblad X1D
- **Lenses**: Canon 85mm f/1.2L, Nikon 50mm f/1.4, Zeiss Otus 55mm f/1.4
- **Terms**: f-stop, bokeh, DOF, shutter speed, ISO

### 🎬 VIDEO/CINEMA CAMERAS & LENSES
- **Cameras**: ARRI Alexa, RED Dragon, Blackmagic URSA, Sony FX9
- **Lenses**: Zeiss Master Primes, Cooke S4/i, Angenieux zooms
- **Terms**: T-stop, dolly, crane, tracking, steadicam

Remember: Using the correct camera type creates more authentic and professional results!

---

{camera_knowledge}
"""