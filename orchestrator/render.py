"""
Rendering and composition system for beat-by-beat video generation.
Uses Manim for individual beats and FFmpeg concat demuxer for final composition.
"""

import subprocess
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import toml

from orchestrator.schemas import AnimationCodegenSchema


class ManimRenderer:
    """Renders individual Manim scenes to video"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config = toml.load(config_path)["manim"]
        self.project_dir = Path("manim_project")
        self.scenes_dir = self.project_dir / "scenes"
        self.output_dir = self.project_dir / "out"
        
        # Ensure directories exist
        self.scenes_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def render_beat(self, scene_code: str, scene_class_name: str, beat_id: int, quality: str = "high") -> Optional[Path]:
        """Render a single beat to MP4"""
        
        # Write scene file
        scene_file = self.scenes_dir / f"beat_{beat_id:04d}.py"
        scene_file.write_text(scene_code, encoding='utf-8')
        
        # Prepare manim command
        quality_flag = self._get_quality_flag(quality)
        output_name = f"beat_{beat_id:04d}"
        
        cmd = [
            "manim",
            quality_flag,
            f"--fps={self.config['fps']}",
            f"--output_file={output_name}",
            str(scene_file),
            scene_class_name
        ]
        
        try:
            print(f"Rendering beat {beat_id}...")
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per beat
            )
            
            if result.returncode != 0:
                print(f"Manim error for beat {beat_id}:")
                print(result.stderr)
                return None
            
            # Find the output file
            output_file = self._find_output_file(beat_id, quality)
            if output_file and output_file.exists():
                print(f"Beat {beat_id} rendered successfully: {output_file}")
                return output_file
            else:
                print(f"Output file not found for beat {beat_id}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"Timeout rendering beat {beat_id}")
            return None
        except Exception as e:
            print(f"Error rendering beat {beat_id}: {e}")
            return None
    
    def render_all_beats(self, codegen: AnimationCodegenSchema, quality: str = "high") -> List[Path]:
        """Render all beats in the codegen schema"""
        
        output_files = []
        
        for i, scene in enumerate(codegen.scenes):
            beat_id = i + 1
            output_file = self.render_beat(scene.code, scene.class_name, beat_id, quality)
            
            if output_file:
                output_files.append(output_file)
            else:
                print(f"Failed to render beat {beat_id}, stopping...")
                break
        
        return output_files
    
    def _get_quality_flag(self, quality: str) -> str:
        """Map quality setting to manim flag"""
        quality_map = {
            "low": "-ql",
            "medium": "-qm", 
            "high": "-qh",
            "4k": "-qk"
        }
        return quality_map.get(quality, "-qh")
    
    def _find_output_file(self, beat_id: int, quality: str) -> Optional[Path]:
        """Find the rendered output file"""
        
        # Manim output structure varies by quality
        quality_dirs = {
            "low": "480p15",
            "medium": "720p30",
            "high": "1080p60",
            "4k": "2160p60"
        }
        
        quality_dir = quality_dirs.get(quality, "1080p60")
        video_dir = self.project_dir / "media" / "videos" / f"beat_{beat_id:04d}" / quality_dir
        
        # Look for MP4 file
        if video_dir.exists():
            mp4_files = list(video_dir.glob("*.mp4"))
            if mp4_files:
                return mp4_files[0]
        
        return None


class VideoComposer:
    """Composes individual beat videos into final video using FFmpeg"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config = toml.load(config_path)["ffmpeg"]
        self.compose_dir = Path("compose")
        self.lists_dir = self.compose_dir / "lists"
        self.output_dir = self.compose_dir / "out"
        
        # Ensure directories exist
        self.lists_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def compose_video(self, beat_files: List[Path], output_name: str = "final_video") -> Optional[Path]:
        """Compose beat videos into final video using concat demuxer"""
        
        if not beat_files:
            print("No beat files to compose")
            return None
        
        # Create concat list file
        list_file = self.lists_dir / f"{output_name}_list.txt"
        self._create_concat_list(beat_files, list_file)
        
        # Output file path
        output_file = self.output_dir / f"{output_name}.mp4"
        
        # First pass: concat without re-encoding if possible
        concat_result = self._concat_demuxer(list_file, output_file)
        
        if concat_result:
            # Optional: final encode with NVENC if configured
            if self.config.get("output_codec") == "h264_nvenc":
                final_file = self.output_dir / f"{output_name}_final.mp4"
                nvenc_result = self._nvenc_encode(output_file, final_file)
                if nvenc_result:
                    return final_file
            
            return output_file
        
        return None
    
    def _create_concat_list(self, beat_files: List[Path], list_file: Path):
        """Create FFmpeg concat demuxer list file"""
        
        with open(list_file, 'w') as f:
            for beat_file in beat_files:
                # Ensure absolute path for FFmpeg
                abs_path = beat_file.resolve()
                f.write(f"file '{abs_path}'\n")
        
        print(f"Created concat list: {list_file}")
    
    def _concat_demuxer(self, list_file: Path, output_file: Path) -> bool:
        """Concatenate videos using FFmpeg concat demuxer (no re-encoding)"""
        
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",  # Copy streams without re-encoding
            "-y",  # Overwrite output
            str(output_file)
        ]
        
        try:
            print(f"Concatenating videos to {output_file}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"FFmpeg concat error:")
                print(result.stderr)
                return False
            
            print(f"Concatenation successful: {output_file}")
            return True
            
        except subprocess.TimeoutExpired:
            print("Timeout during video concatenation")
            return False
        except Exception as e:
            print(f"Error during concatenation: {e}")
            return False
    
    def _nvenc_encode(self, input_file: Path, output_file: Path) -> bool:
        """Final encode with NVENC for optimal distribution"""
        
        cmd = [
            "ffmpeg",
            "-i", str(input_file),
            "-c:v", self.config["output_codec"],
            "-preset", self.config["preset"],
            "-tune", "hq",  # High quality tune for NVENC
            "-crf", str(self.config["crf"]),
            "-pix_fmt", self.config["pixel_format"],
            "-bf", "3",  # B-frames for better compression
            "-b_ref_mode", "middle",  # Reference frame mode
            "-spatial_aq", "1",  # Spatial adaptive quantization
            "-temporal_aq", "1",  # Temporal adaptive quantization
            "-rc_lookahead", "20",  # Rate control lookahead
            "-y"
        ]
        
        # Add audio normalization if enabled
        if self.config.get("audio_normalize", True):
            cmd.extend([
                "-af", f"loudnorm=I={self.config.get('loudnorm_i', -16)}:"
                       f"TP={self.config.get('loudnorm_tp', -1.5)}:"
                       f"LRA={self.config.get('loudnorm_lra', 11)}"
            ])
        
        # Add faststart if configured
        if self.config.get("enable_faststart", True):
            cmd.extend(["-movflags", "+faststart"])
        
        cmd.append(str(output_file))
        
        try:
            print(f"NVENC encoding with loudness normalization to {output_file}...")
            print(f"NVENC preset: {self.config['preset']}, CRF: {self.config['crf']}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for encoding
            )
            
            if result.returncode != 0:
                print(f"NVENC encoding error:")
                print(result.stderr)
                return False
            
            print(f"NVENC encoding successful: {output_file}")
            return True
            
        except subprocess.TimeoutExpired:
            print("Timeout during NVENC encoding")
            return False
        except Exception as e:
            print(f"Error during NVENC encoding: {e}")
            return False
    
    def compose_with_transitions(self, beat_files: List[Path], output_name: str = "final_video", 
                               transition_duration: float = 0.5) -> Optional[Path]:
        """Compose videos with crossfade transitions and loudness normalization"""
        
        if not beat_files:
            print("No beat files to compose")
            return None
        
        if len(beat_files) == 1:
            # Single file, just copy with normalization
            output_file = self.output_dir / f"{output_name}.mp4"
            return self._nvenc_encode(beat_files[0], output_file) and output_file or None
        
        # Build complex filter for crossfades
        output_file = self.output_dir / f"{output_name}_transitions.mp4"
        
        # Create input list
        inputs = []
        for beat_file in beat_files:
            inputs.extend(["-i", str(beat_file)])
        
        # Build filter complex for crossfades
        filter_parts = []
        video_parts = []
        audio_parts = []
        
        for i in range(len(beat_files)):
            if i == 0:
                # First video - no transition in
                video_parts.append(f"[{i}:v]")
                audio_parts.append(f"[{i}:a]")
            else:
                # Add crossfade transition
                prev_video = video_parts[-1] if video_parts else f"[{i-1}:v]"
                curr_video = f"[{i}:v]"
                
                xfade_output = f"[v{i}]"
                filter_parts.append(f"{prev_video}{curr_video}xfade=transition=fade:duration={transition_duration}:offset=...{xfade_output}")
                video_parts = [xfade_output]
                
                # Audio crossfade
                prev_audio = audio_parts[-1] if audio_parts else f"[{i-1}:a]"
                curr_audio = f"[{i}:a]"
                acrossfade_output = f"[a{i}]"
                filter_parts.append(f"{prev_audio}{curr_audio}acrossfade=d={transition_duration}{acrossfade_output}")
                audio_parts = [acrossfade_output]
        
        # Combine filter parts
        filter_complex = ";".join(filter_parts)
        final_video = video_parts[0] if video_parts else "[0:v]"
        final_audio = audio_parts[0] if audio_parts else "[0:a]"
        
        cmd = [
            "ffmpeg"
        ] + inputs + [
            "-filter_complex", filter_complex,
            "-map", final_video,
            "-map", final_audio,
            "-c:v", self.config["output_codec"],
            "-preset", self.config["preset"],
            "-tune", "hq",
            "-crf", str(self.config["crf"]),
            "-af", f"loudnorm=I={self.config.get('loudnorm_i', -16)}:"
                   f"TP={self.config.get('loudnorm_tp', -1.5)}:"
                   f"LRA={self.config.get('loudnorm_lra', 11)}",
            "-y",
            str(output_file)
        ]
        
        try:
            print(f"Creating video with transitions...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout for complex operations
            )
            
            if result.returncode != 0:
                print(f"Transition composition error:")
                print(result.stderr)
                return None
            
            print(f"Transition composition successful: {output_file}")
            return output_file
            
        except subprocess.TimeoutExpired:
            print("Timeout during transition composition")
            return None
        except Exception as e:
            print(f"Error during transition composition: {e}")
            return None
    
    def validate_streams(self, beat_files: List[Path]) -> bool:
        """Validate that all beat files have compatible streams for concat"""
        
        if not beat_files:
            return False
        
        # Get stream info for first file as reference
        reference_info = self._get_stream_info(beat_files[0])
        if not reference_info:
            return False
        
        # Check all other files match
        for beat_file in beat_files[1:]:
            stream_info = self._get_stream_info(beat_file)
            if not stream_info:
                return False
            
            # Check critical parameters match
            if (stream_info['codec'] != reference_info['codec'] or
                stream_info['width'] != reference_info['width'] or
                stream_info['height'] != reference_info['height'] or
                abs(float(stream_info['fps']) - float(reference_info['fps'])) > 0.1):
                
                print(f"Stream mismatch detected in {beat_file}")
                print(f"Expected: {reference_info}")
                print(f"Got: {stream_info}")
                return False
        
        return True
    
    def _get_stream_info(self, video_file: Path) -> Optional[Dict[str, str]]:
        """Get video stream information using ffprobe"""
        
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-select_streams", "v:0",  # First video stream
            str(video_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            if not data.get('streams'):
                return None
            
            stream = data['streams'][0]
            return {
                'codec': stream.get('codec_name', ''),
                'width': stream.get('width', 0),
                'height': stream.get('height', 0),
                'fps': stream.get('r_frame_rate', '0/1').split('/')[0]
            }
            
        except Exception:
            return None