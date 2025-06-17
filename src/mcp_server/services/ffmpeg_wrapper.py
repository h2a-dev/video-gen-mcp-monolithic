"""FFmpeg wrapper service for video processing."""

import os
import asyncio
import json
import sys
import platform
import shutil
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
        """Concatenate multiple videos with dynamic transitions by trimming first 0.5 seconds from clips starting from the second one."""
        try:
            # Check if videos have audio streams
            has_audio = True
            if video_paths:
                first_video_info = await self.get_video_info(video_paths[0])
                if first_video_info.get("error") or not first_video_info.get("has_audio", True):
                    has_audio = False
                print(f"[FFmpeg] Videos have audio: {has_audio}", file=sys.stderr)
            
            if len(video_paths) == 1:
                # Single video, just copy
                cmd = [
                    self.ffmpeg_path,
                    "-i", video_paths[0],
                    "-c:v", "copy",
                    "-c:a", "copy" if has_audio else "-an",
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path)
                ]
                
                result = await self._run_ffmpeg(cmd, timeout=300)
            else:
                # Multiple videos - trim and concatenate
                # First, create trimmed versions using simple -ss
                trimmed_paths = []
                temp_files_created = []
                
                for i, video_path in enumerate(video_paths):
                    if i == 0:
                        # First video - use as is
                        trimmed_paths.append(video_path)
                    else:
                        # Trim first 0.5 seconds using -ss
                        trimmed_path = settings.temp_dir / f"trimmed_{os.getpid()}_{i}.mp4"
                        temp_files_created.append(trimmed_path)
                        
                        trim_cmd = [
                            self.ffmpeg_path,
                            "-ss", "0.5",  # Skip first 0.5 seconds
                            "-i", str(video_path),
                            "-c:v", "copy",  # Copy codec!
                            "-c:a", "copy" if has_audio else "-an",
                            "-avoid_negative_ts", "make_zero",  # Handle timestamp issues
                            "-y",
                            str(trimmed_path)
                        ]
                        
                        trim_result = await self._run_ffmpeg(trim_cmd)
                        if trim_result.get("success"):
                            trimmed_paths.append(str(trimmed_path))
                            print(f"[FFmpeg] Successfully trimmed video {i}", file=sys.stderr)
                        else:
                            # If trimming fails, use original
                            print(f"[FFmpeg] Trim failed for video {i}, using original", file=sys.stderr)
                            trimmed_paths.append(video_path)
                
                # Now concatenate using the concat demuxer
                concat_file = settings.temp_dir / f"concat_{os.getpid()}.txt"
                temp_files_created.append(concat_file)
                
                with open(concat_file, 'w') as f:
                    for path in trimmed_paths:
                        # Use absolute paths and escape single quotes
                        escaped_path = str(Path(path).resolve()).replace("'", "'\\''")
                        f.write(f"file '{escaped_path}'\n")
                
                concat_cmd = [
                    self.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_file),
                    "-c", "copy",  # Copy everything!
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path)
                ]
                
                result = await self._run_ffmpeg(concat_cmd, timeout=300)
                
                # Clean up temp files
                for temp_file in temp_files_created:
                    try:
                        if temp_file.exists():
                            temp_file.unlink()
                    except:
                        pass
            
            if not result.get("success", False):
                return result
            
            # Get output info
            output_info = await self.get_video_info(output_path)
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": output_info.get("duration", 0),
                "size": os.path.getsize(output_path),
                "trimmed_seconds": 0.5 * (len(video_paths) - 1),
                "command": " ".join(concat_cmd if 'concat_cmd' in locals() else cmd)
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
        """Add audio track to video, mixing with existing audio if present."""
        try:
            # Check if video has existing audio
            video_info = await self.get_video_info(video_path)
            has_existing_audio = video_info.get("has_audio", False)
            
            if has_existing_audio:
                # Mix audio tracks using amix filter
                # Build audio filters for new track
                new_audio_filters = []
                if audio_volume != 1.0:
                    new_audio_filters.append(f"volume={audio_volume}")
                if fade_in > 0:
                    new_audio_filters.append(f"afade=t=in:d={fade_in}")
                if fade_out > 0:
                    new_audio_filters.append(f"afade=t=out:d={fade_out}")
                
                # Create filter complex to mix both audio streams
                # Use 'sum' mode instead of default 'average' to prevent volume loss
                filter_parts = []
                if new_audio_filters:
                    filter_parts.append(f"[1:a]{','.join(new_audio_filters)}[a1]")
                    # Use dropout_transition=0 to prevent volume changes when one stream ends
                    filter_parts.append("[0:a][a1]amix=inputs=2:duration=longest:dropout_transition=0:weights='1 1'[aout]")
                else:
                    filter_parts.append("[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0:weights='1 1'[aout]")
                
                filter_complex = ";".join(filter_parts)
                
                # Build command with audio mixing
                cmd = [
                    self.ffmpeg_path,
                    "-i", str(video_path),
                    "-i", str(audio_path),
                    "-filter_complex", filter_complex,
                    "-map", "0:v",     # Video from first input
                    "-map", "[aout]",  # Mixed audio output
                    "-c:v", "copy",    # Copy video stream
                    "-c:a", "aac",     # Encode audio
                    "-b:a", "192k",
                    "-y",
                    str(output_path)
                ]
            else:
                # No existing audio, just add the new track
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
            
            # Log the command for debugging
            print(f"[FFmpeg] add_audio_track command: {' '.join(cmd)}", file=sys.stderr)
            
            # Execute command
            result = await self._run_ffmpeg(cmd, timeout=60)
            
            if not result.get("success", False):
                return result
            
            # Verify the output has audio
            output_info = await self.get_video_info(output_path)
            print(f"[FFmpeg] Output has audio: {output_info.get('has_audio', False)}", file=sys.stderr)
            
            return {
                "success": True,
                "output_path": output_path,
                "size": os.path.getsize(output_path),
                "audio_filters": audio_filters if not has_existing_audio else new_audio_filters,
                "mixed_audio": has_existing_audio,
                "command": " ".join(cmd)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_multiple_audio_tracks(
        self,
        video_path: str,
        audio_tracks: List[Dict[str, Any]],
        output_path: str
    ) -> Dict[str, Any]:
        """Add multiple audio tracks to video at once, mixing them together.
        
        Args:
            video_path: Path to input video
            audio_tracks: List of dicts with keys:
                - path: Audio file path
                - volume: Volume level (0.0-2.0)
                - type: 'voiceover' or 'music'
            output_path: Path for output video
        """
        try:
            if not audio_tracks:
                return {
                    "success": False,
                    "error": "No audio tracks provided"
                }
            
            # Start building the command
            cmd = [self.ffmpeg_path, "-i", str(video_path)]
            
            # Add all audio inputs
            for track in audio_tracks:
                cmd.extend(["-i", str(track["path"])])
            
            # Build filter complex for mixing all audio tracks
            filter_parts = []
            audio_inputs = []
            
            # Apply volume to each audio track
            for i, track in enumerate(audio_tracks):
                audio_idx = i + 1  # 0 is the video
                volume = track.get("volume", 1.0)
                
                if volume != 1.0:
                    filter_parts.append(f"[{audio_idx}:a]volume={volume}[a{i}]")
                    audio_inputs.append(f"[a{i}]")
                else:
                    audio_inputs.append(f"[{audio_idx}:a]")
            
            # Mix all audio tracks
            if len(audio_tracks) == 1:
                # Single track, no mixing needed
                if filter_parts:
                    filter_complex = ";".join(filter_parts)
                    audio_output = audio_inputs[0]
                else:
                    filter_complex = None
                    audio_output = "1:a"
            else:
                # Multiple tracks, mix them
                if filter_parts:
                    filter_complex = ";".join(filter_parts) + ";"
                else:
                    filter_complex = ""
                
                # Use amix with weights to preserve volume
                weights = " ".join(["1" for _ in audio_tracks])
                filter_complex += f"{''.join(audio_inputs)}amix=inputs={len(audio_tracks)}:duration=longest:dropout_transition=0:weights='{weights}'[aout]"
                audio_output = "[aout]"
            
            # Complete the command
            if filter_complex:
                cmd.extend(["-filter_complex", filter_complex])
            
            cmd.extend([
                "-map", "0:v",          # Video from first input
                "-map", audio_output,   # Mixed audio
                "-c:v", "copy",         # Copy video stream
                "-c:a", "aac",          # Encode audio
                "-b:a", "192k",
                "-y",
                str(output_path)
            ])
            
            print(f"[FFmpeg] Mixing {len(audio_tracks)} audio tracks", file=sys.stderr)
            for track in audio_tracks:
                print(f"[FFmpeg]   - {track.get('type', 'unknown')}: volume={track.get('volume', 1.0)}", file=sys.stderr)
            
            # Execute command
            result = await self._run_ffmpeg(cmd, timeout=120)
            
            if not result.get("success", False):
                return result
            
            return {
                "success": True,
                "output_path": output_path,
                "size": os.path.getsize(output_path),
                "tracks_mixed": len(audio_tracks),
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
                    "codec": "copy",
                    "preset": "slow",
                    "crf": "18",
                    "audio_bitrate": "384k"
                },
                "tiktok": {
                    "codec": "copy",
                    "preset": "medium",
                    "crf": "23",
                    "audio_bitrate": "256k",
                    "max_size": "287M"  # TikTok limit
                },
                "instagram_reel": {
                    "codec": "copy",
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
                "-i", str(input_path)
            ]
            
            # Add watermark if requested
            if include_watermark and watermark_text:
                filter_text = f"drawtext=text='{watermark_text}':fontcolor=white:fontsize=24:x=10:y=10"
                cmd.extend([
                    "-vf", filter_text,
                    "-c:v", "libx264",  # Must re-encode when adding watermark
                    "-preset", "fast",
                    "-crf", "23"
                ])
            else:
                cmd.extend(["-c:v", "copy"])  # Copy when no filters
            
            cmd.extend([
                "-c:a", "aac",
                "-b:a", settings["audio_bitrate"],
                "-movflags", "+faststart",
                "-y"
            ])
            
            # Add size limit if specified
            if "max_size" in settings:
                cmd.extend(["-fs", settings["max_size"]])
            
            cmd.append(str(output_path))
            
            # Execute command
            result = await self._run_ffmpeg(cmd, timeout=60)
            
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
            # Get appropriate ffprobe command for platform
            ffprobe_cmd = self._get_ffprobe_command()
            cmd = [
                ffprobe_cmd,
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
    
    async def _run_ffmpeg(self, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
        """Run ffmpeg command asynchronously with timeout and progress monitoring."""
        try:
            # Log the command being executed
            print(f"[FFmpeg] Executing: {' '.join(cmd[:3])}...", file=sys.stderr)
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                # Wait for process with timeout
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                proc.kill()
                await proc.wait()
                raise RuntimeError(f"FFmpeg timed out after {timeout} seconds")
            
            if proc.returncode != 0:
                # Include more stderr for debugging (but still limit to prevent overflow)
                error_msg = stderr.decode()[:2000]
                raise RuntimeError(
                    f"FFmpeg failed with code {proc.returncode}: {error_msg}"
                )
            
            return {
                "success": True,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
            
        except Exception as e:
            print(f"[FFmpeg] Error: {str(e)}", file=sys.stderr)
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
    
    def _get_ffprobe_command(self) -> str:
        """Get the appropriate ffprobe command for the current platform."""
        # Check if custom FFPROBE_PATH is set
        custom_path = os.getenv("FFPROBE_PATH")
        if custom_path:
            return custom_path
        
        # Determine the executable name based on platform
        if platform.system() == "Windows":
            ffprobe_name = "ffprobe.exe"
        else:
            ffprobe_name = "ffprobe"
        
        # Check if ffprobe is in PATH
        ffprobe_in_path = shutil.which(ffprobe_name)
        if ffprobe_in_path:
            return ffprobe_in_path
        
        # Return the default name
        return ffprobe_name


# Singleton instance
ffmpeg_wrapper = FFmpegWrapper()