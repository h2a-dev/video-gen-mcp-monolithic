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

## 🎬 Quick Cinematic Formulas

### Opening Shot (Establishing)
```
"{{description}}, shot on ARRI Alexa, 24mm wide angle lens, cinematic widescreen, 
golden hour lighting, crane shot rising, professional cinematography"
```

### Character/Portrait Scenes
```
"{{description}}, Canon 85mm f/1.2L, shallow depth of field, creamy bokeh, 
shot on Canon 5D Mark IV, natural window lighting, eye-level angle"
```

### Action Sequences
```
"{{description}}, 70-200mm f/2.8 telephoto, 1/1000s shutter speed, frozen motion,
compressed perspective, handheld documentary style, high contrast"
```

### Emotional/Intimate Moments
```
"{{description}}, 50mm f/1.2, intimate framing, soft lighting, 
Kodak Portra 400 film aesthetic, subtle handheld movement"
```

### Closing Shot
```
"{{description}}, anamorphic lens, blue hour lighting, slow dolly out,
cinematic color grading, wide establishing shot, ethereal atmosphere"
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

### After (Cinematic):
"A cozy coffee shop interior, shot on Canon 5D Mark IV, 35mm f/1.4 lens, 
warm window lighting, shallow depth of field, steam rising from coffee cups, 
cinematic composition, professional photography"

### Before (Motion):
"Camera moves forward"

### After (Cinematic Motion):
"Smooth dolly forward, steadicam glide through the coffee shop, 
subtle parallax between foreground and background elements, 
gradual focus pull from cups to barista, cinematic movement"

## 🎨 Style Combinations

### Documentary Style
"Handheld camera, natural lighting, raw authentic feel, Canon C300, 
24-70mm zoom lens, observational framing"

### Vintage Film
"Shot on Hasselblad 500CM, Kodak Portra 400, medium format, 
film grain, slightly desaturated colors, nostalgic mood"

### Modern Commercial
"Sony A7R IV, crystal clear 8K quality, professional studio lighting,
product photography aesthetic, clean composition"

### Artistic/Experimental
"Double exposure effect, tilt-shift lens, selective focus,
light leaks, experimental framing, artistic interpretation"

## 🚀 Quick Implementation

To use these enhancements:
1. Take your base description
2. Add camera/lens details for authenticity
3. Include lighting description for mood
4. Add movement terms for video
5. Specify composition style

Remember: The AI responds well to specific technical details that create a cohesive visual style!

---

{camera_knowledge}
"""