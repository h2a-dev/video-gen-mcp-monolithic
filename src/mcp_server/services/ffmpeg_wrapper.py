"""FFmpeg wrapper service for video processing."""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import subprocess
from ..config import settings


class FFmpegWrapper:
    """Wrapper for FFmpeg operations."""
    
    def __init__(self):
        self.ffmpeg_path = settings.ffmpeg_path
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            subprocess.run([self.ffmpeg_path, "-version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                f"FFmpeg not found at '{self.ffmpeg_path}'. "
                "Please install FFmpeg or set FFMPEG_PATH environment variable."
            )
    
    async def concat_videos(
        self,
        video_paths: List[str],
        output_path: str,
        quality_preset: str = "high"
    ) -> Dict[str, Any]:
        """Concatenate multiple videos with dynamic transitions by trimming first 15 frames from clips starting from the second one."""
        try:
            # Quality presets
            quality_settings = {
                "low": {"crf": 28, "preset": "faster"},
                "medium": {"crf": 23, "preset": "medium"},
                "high": {"crf": 18, "preset": "slow"}
            }
            
            q = quality_settings.get(quality_preset, quality_settings["high"])
            
            # Check if videos have audio streams
            has_audio = True
            for video_path in video_paths:
                info = await self.get_video_info(video_path)
                if info.get("error") or not info.get("has_audio", True):
                    has_audio = False
                    break
            
            # For dynamic transitions, we need to use filter_complex
            # Build filter complex string for trimming and concatenation
            filter_parts = []
            concat_inputs = []
            
            for i, video_path in enumerate(video_paths):
                if i == 0:
                    # First video - use as is
                    concat_inputs.append(f"[{i}:v]")
                    if has_audio:
                        concat_inputs.append(f"[{i}:a]")
                else:
                    # Subsequent videos - trim first 15 frames (approximately 0.5 seconds at 30fps)
                    # We'll use trim to drop frames and create a more dynamic transition
                    filter_parts.append(f"[{i}:v]trim=start_frame=15,setpts=PTS-STARTPTS[v{i}]")
                    concat_inputs.append(f"[v{i}]")
                    if has_audio:
                        filter_parts.append(f"[{i}:a]atrim=start=0.5,asetpts=PTS-STARTPTS[a{i}]")
                        concat_inputs.append(f"[a{i}]")
            
            # Create the full filter complex
            if len(video_paths) == 1:
                # Single video, no trimming needed
                cmd = [
                    self.ffmpeg_path,
                    "-i", video_paths[0],
                    "-c:v", "libx264",
                    "-preset", q["preset"],
                    "-crf", str(q["crf"]),
                    "-pix_fmt", "yuv420p"
                ]
                
                if has_audio:
                    cmd.extend(["-c:a", "aac", "-b:a", "192k"])
                else:
                    cmd.extend(["-an"])  # No audio
                
                cmd.extend([
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path)
                ])
            else:
                # Multiple videos with trimming
                if filter_parts:
                    filter_complex = ";".join(filter_parts) + ";"
                else:
                    filter_complex = ""
                
                # Add concatenation
                if has_audio:
                    filter_complex += "".join(concat_inputs) + f"concat=n={len(video_paths)}:v=1:a=1[outv][outa]"
                else:
                    filter_complex += "".join(concat_inputs) + f"concat=n={len(video_paths)}:v=1:a=0[outv]"
                
                # Build command with filter_complex
                cmd = [self.ffmpeg_path]
                
                # Add all input files
                for video_path in video_paths:
                    cmd.extend(["-i", str(video_path)])
                
                # Add filter complex
                cmd.extend([
                    "-filter_complex", filter_complex,
                    "-map", "[outv]"
                ])
                
                if has_audio:
                    cmd.extend([
                        "-map", "[outa]",
                        "-c:a", "aac",
                        "-b:a", "192k"
                    ])
                else:
                    cmd.extend(["-an"])  # No audio
                
                cmd.extend([
                    "-c:v", "libx264",
                    "-preset", q["preset"],
                    "-crf", str(q["crf"]),
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path)
                ])
            
            # Execute command
            result = await self._run_ffmpeg(cmd)
            
            if not result.get("success", False):
                # If complex filter fails, try simpler approach
                # Create temp files for trimmed videos
                trimmed_paths = []
                for i, video_path in enumerate(video_paths):
                    if i == 0:
                        trimmed_paths.append(video_path)
                    else:
                        # Trim first 15 frames from this video
                        trimmed_path = settings.temp_dir / f"trimmed_{os.getpid()}_{i}.mp4"
                        trim_cmd = [
                            self.ffmpeg_path,
                            "-i", str(video_path),
                            "-vf", "select='gte(n\\,15)',setpts=PTS-STARTPTS",
                            "-c:v", "libx264",
                            "-preset", "fast",
                            "-crf", "23"
                        ]
                        
                        if has_audio:
                            trim_cmd.extend([
                                "-af", "atrim=start=0.5,asetpts=PTS-STARTPTS",
                                "-c:a", "aac"
                            ])
                        else:
                            trim_cmd.append("-an")
                        
                        trim_cmd.extend(["-y", str(trimmed_path)])
                        
                        trim_result = await self._run_ffmpeg(trim_cmd)
                        if trim_result.get("success"):
                            trimmed_paths.append(str(trimmed_path))
                        else:
                            # If trimming fails, use original
                            trimmed_paths.append(video_path)
                
                # Now concatenate the trimmed videos
                concat_file = settings.temp_dir / f"concat_{os.getpid()}.txt"
                with open(concat_file, 'w') as f:
                    for path in trimmed_paths:
                        f.write(f"file '{path}'\n")
                
                concat_cmd = [
                    self.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_file),
                    "-c:v", "libx264",
                    "-preset", q["preset"],
                    "-crf", str(q["crf"]),
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path)
                ]
                
                result = await self._run_ffmpeg(concat_cmd)
                
                # Clean up temp files
                concat_file.unlink(missing_ok=True)
                for i, path in enumerate(trimmed_paths):
                    if i > 0 and path != video_paths[i]:
                        Path(path).unlink(missing_ok=True)
            
            if not result.get("success", False):
                return result
            
            # Get output info
            output_info = await self.get_video_info(output_path)
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": output_info.get("duration", 0),
                "size": os.path.getsize(output_path),
                "trimmed_frames": 15 * (len(video_paths) - 1),
                "command": " ".join(cmd) if isinstance(cmd, list) else cmd
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_audio_track(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        audio_volume: float = 1.0,
        fade_in: float = 0.0,
        fade_out: float = 0.0
    ) -> Dict[str, Any]:
        """Add audio track to video without re-encoding video stream."""
        try:
            # Build audio filters
            audio_filters = []
            if audio_volume != 1.0:
                audio_filters.append(f"volume={audio_volume}")
            if fade_in > 0:
                audio_filters.append(f"afade=t=in:d={fade_in}")
            if fade_out > 0:
                audio_filters.append(f"afade=t=out:d={fade_out}")
            
            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",  # Copy video stream
                "-c:a", "aac",   # Encode audio
                "-b:a", "192k",
                "-map", "0:v",   # Video from first input
                "-map", "1:a",   # Audio from second input
                "-shortest",     # Stop when shortest stream ends
                "-y",
                str(output_path)
            ]
            
            # Add audio filters if any
            if audio_filters:
                filter_str = ",".join(audio_filters)
                cmd.insert(-1, "-af")
                cmd.insert(-1, filter_str)
            
            # Execute command
            result = await self._run_ffmpeg(cmd)
            
            return {
                "success": True,
                "output_path": output_path,
                "size": os.path.getsize(output_path),
                "audio_filters": audio_filters,
                "command": " ".join(cmd)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def export_for_platform(
        self,
        input_path: str,
        output_path: str,
        platform: str,
        include_watermark: bool = False,
        watermark_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export video optimized for specific platform."""
        try:
            # Platform-specific settings
            platform_settings = {
                "youtube": {
                    "codec": "libx264",
                    "preset": "slow",
                    "crf": "18",
                    "audio_bitrate": "384k"
                },
                "tiktok": {
                    "codec": "libx264",
                    "preset": "medium",
                    "crf": "23",
                    "audio_bitrate": "256k",
                    "max_size": "287M"  # TikTok limit
                },
                "instagram_reel": {
                    "codec": "libx264",
                    "preset": "medium",
                    "crf": "23",
                    "audio_bitrate": "256k",
                    "max_size": "100M"
                }
            }
            
            settings = platform_settings.get(platform, platform_settings["youtube"])
            
            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", str(input_path),
                "-c:v", settings["codec"],
                "-preset", settings["preset"],
                "-crf", settings["crf"],
                "-c:a", "aac",
                "-b:a", settings["audio_bitrate"],
                "-pix_fmt", "yuv420p",  # Compatibility
                "-movflags", "+faststart",
                "-y"
            ]
            
            # Add watermark if requested
            if include_watermark and watermark_text:
                filter_text = f"drawtext=text='{watermark_text}':fontcolor=white:fontsize=24:x=10:y=10"
                cmd.extend(["-vf", filter_text])
            
            # Add size limit if specified
            if "max_size" in settings:
                cmd.extend(["-fs", settings["max_size"]])
            
            cmd.append(str(output_path))
            
            # Execute command
            result = await self._run_ffmpeg(cmd)
            
            # Get output info
            output_info = await self.get_video_info(output_path)
            
            return {
                "success": True,
                "output_path": output_path,
                "platform": platform,
                "size": os.path.getsize(output_path),
                "size_mb": round(os.path.getsize(output_path) / (1024 * 1024), 2),
                "duration": output_info.get("duration", 0),
                "settings_used": settings,
                "command": " ".join(cmd)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_path)
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {stderr.decode()}")
            
            data = json.loads(stdout.decode())
            
            # Extract key information
            format_info = data.get("format", {})
            streams = data.get("streams", [])
            
            video_stream = next(
                (s for s in streams if s["codec_type"] == "video"),
                {}
            )
            
            audio_stream = next(
                (s for s in streams if s["codec_type"] == "audio"),
                None
            )
            
            # Calculate fps safely
            fps = 0
            if video_stream.get("r_frame_rate"):
                try:
                    num, den = video_stream["r_frame_rate"].split("/")
                    fps = float(num) / float(den) if float(den) != 0 else 0
                except:
                    fps = 0
            
            return {
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "bit_rate": int(format_info.get("bit_rate", 0)),
                "width": video_stream.get("width", 0),
                "height": video_stream.get("height", 0),
                "fps": round(fps, 2),
                "codec": video_stream.get("codec_name", "unknown"),
                "has_audio": audio_stream is not None,
                "audio_codec": audio_stream.get("codec_name", "none") if audio_stream else "none"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _run_ffmpeg(self, cmd: List[str]) -> Dict[str, Any]:
        """Run ffmpeg command asynchronously."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg failed with code {proc.returncode}: {stderr.decode()}"
                )
            
            return {
                "success": True,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
            
        except Exception as e:
            raise RuntimeError(f"FFmpeg execution failed: {str(e)}")
    
    def get_aspect_ratio_filter(self, aspect_ratio: str) -> str:
        """Get ffmpeg filter for aspect ratio adjustment."""
        ratios = {
            "16:9": "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "9:16": "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "1:1": "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2",
            "4:5": "scale=864:1080:force_original_aspect_ratio=decrease,pad=864:1080:(ow-iw)/2:(oh-ih)/2"
        }
        return ratios.get(aspect_ratio, ratios["16:9"])


# Singleton instance
ffmpeg_wrapper = FFmpegWrapper()