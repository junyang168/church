import os
import math
import json
import tempfile
import logging
from pydub import AudioSegment
from pydub.silence import detect_silence
import openai
from datetime import timedelta
import time
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self,  output_item="transcription"):
        self.openai_client = openai.OpenAI()
        self.output_item = output_item
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Using temporary directory: {self.temp_dir}")


    def split_audio_by_size_at_silence(self, input_file, target_size_mb=10, min_silence_len=500, silence_thresh=-40, search_window_sec=10):
        """
        Split an audio file into chunks of approximately target_size_mb,
        ensuring splits occur during silence between sentences.
        
        Args:
            input_file (str): Path to input audio file
            target_size_mb (int): Target size of each chunk in MB
            min_silence_len (int): Minimum length of silence in ms
            silence_thresh (int): Silence threshold in dB
            search_window_sec (int): How many seconds to search around the split point
        
        Returns:
            list: Paths to the output files
        """
        print(f"Loading audio file: {input_file}")
        audio = AudioSegment.from_file(input_file)
        
        # Calculate file size in bytes per ms of audio
        bytes_per_ms = os.path.getsize(input_file) / len(audio)
        
        # Calculate target chunk duration in ms
        target_chunk_ms = (target_size_mb * 1024 * 1024) / bytes_per_ms
        
        # Number of chunks needed
        total_chunks = math.ceil(len(audio) / target_chunk_ms)
        print(f"Audio length: {len(audio)/1000:.2f} seconds")
        print(f"Approximate chunks needed: {total_chunks}")
        
        output_files = []
        filename, extension = os.path.splitext(input_file)
        
        start_pos = 0
        chunk_number = 1
        chunks = []        
        while start_pos < len(audio):
            # Calculate theoretical end position for this chunk
            theoretical_end = min(start_pos + target_chunk_ms, len(audio))
            
            # If we're at the end of the file, just take what's left
            if theoretical_end >= len(audio) or chunk_number == total_chunks:
                end_pos = len(audio)
            else:
                # Define a window around the theoretical split point to search for silence
                window_size_ms = search_window_sec * 1000
                window_start = max(theoretical_end - window_size_ms//2, start_pos)
                window_end = min(theoretical_end + window_size_ms//2, len(audio))
                
                # Extract just the audio segment in our search window
                search_segment = audio[window_start:window_end]
                
                # Convert audio segment to numpy array for silence detection
                samples = np.array(search_segment.get_array_of_samples())
                
                # Calculate RMS values in chunks of min_silence_len
                chunk_size = int(search_segment.frame_rate * min_silence_len / 1000)
                rms_values = []
                for i in range(0, len(samples), chunk_size):
                    if i + chunk_size <= len(samples):
                        chunk = samples[i:i+chunk_size]
                        rms = np.sqrt(np.mean(chunk**2))
                        rms_values.append((i, rms))
                
                # Find the quietest section
                if rms_values:
                    quietest_chunk_start, _ = min(rms_values, key=lambda x: x[1])
                    
                    # Convert the sample position to milliseconds within the search window
                    quietest_ms_in_window = (quietest_chunk_start / search_segment.frame_rate) * 1000
                    
                    # Add half of the silence length to get to the middle of the quiet section
                    middle_of_silence_ms = quietest_ms_in_window + (min_silence_len / 2)
                    
                    # Add to window_start to get the absolute position in the original audio
                    end_pos = window_start + middle_of_silence_ms
                else:
                    # Fallback if no silence found
                    end_pos = theoretical_end
            
            # Extract the chunk and export
            chunk = audio[start_pos:end_pos]
            chunks.append((chunk, start_pos))
            
            # Move to next chunk
            start_pos = end_pos
            chunk_number += 1
        
        return chunks

            
    
    def save_chunks(self, chunks):
        """
        Save audio chunks to temporary files
        Returns list of (chunk_path, start_time_ms)
        """
        chunk_info = []
        for i, (chunk, start_time) in enumerate(chunks):
            chunk_path = os.path.join(self.temp_dir, f"chunk_{i}.mp3")
            chunk.export(chunk_path, format="mp3")
            chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
            logger.info(f"Saved chunk {i+1}/{len(chunks)} ({chunk_size_mb:.2f}MB) to {chunk_path}")
            chunk_info.append((chunk_path, start_time))
        return chunk_info
    
    def parse_srt(self, srt_text, time_offset_ms=0):
        """
        Parse SRT format to JSON format with correct timestamps adjusted by offset
        """
        entries = []
        blocks = srt_text.strip().split('\n\n')
        time_offset_ms = int(time_offset_ms)
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0])
                timestamp_line = lines[1]
                text = ' '.join(lines[2:])
                
                # Parse timestamps
                start_time_str, end_time_str = timestamp_line.split(' --> ')
                
                # Convert timestamps to milliseconds
                def time_to_ms(time_str):
                    hours, minutes, seconds = time_str.split(':')
                    seconds, milliseconds = seconds.split(',')
                    return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(milliseconds)
                
                start_ms = time_to_ms(start_time_str) + time_offset_ms
                end_ms = time_to_ms(end_time_str) + time_offset_ms
                
                # Convert back to SRT format
                def ms_to_time(ms):
                    seconds, ms = divmod(ms, 1000)
                    minutes, seconds = divmod(seconds, 60)
                    hours, minutes = divmod(minutes, 60)
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"
                
                start_time = ms_to_time(start_ms)
                end_time = ms_to_time(end_ms)
                
                entries.append({
                    "index": index,
                    "start": start_time,
                    "end": end_time,
                    "text": text,
                    "start_ms": start_ms,
                    "end_ms": end_ms
                })
                
            except Exception as e:
                logger.error(f"Error parsing SRT block: {e}")
                continue
                
        return entries
    
    def transcribe_chunks(self, chunk_info):
        """
        Transcribe each chunk using OpenAI Whisper API
        Returns list of subtitle entries with corrected timestamps
        """
        max_retries = 5  # Set a limit on retries
        backoff_factor = 2  # Exponential backoff multiplier
        delay = 1  # Initial delay in seconds
        
        all_entries = []        
        success = True
        for i, (chunk_path, start_time_ms) in enumerate(chunk_info):
            logger.info(f"Transcribing chunk {i+1}/{len(chunk_info)}")
            
            with open(chunk_path, "rb") as audio_file:
                for attempt in range(max_retries):
                    try:
                        response = self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="srt"        
                        )
                        
                        # Parse SRT and adjust timestamps based on chunk start time
                        entries = self.parse_srt(response, time_offset_ms=start_time_ms)
                        
                        # Add chunk information to entries
                        for entry in entries:
                            entry["chunk"] = i + 1
                        
                        all_entries.extend(entries)
                        success = True
                        logger.info(f"Successfully transcribed chunk {i+1} with {len(entries)} subtitles")
                        break
                    except openai.RateLimitError as e:
                        print(f"Rate limit exceeded. Attempt {attempt + 1} of {max_retries}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= backoff_factor  # Increase wait time exponentially
                        success = False
                    except openai.APIError as e:
                        logger.error(f"OpenAI API error: {str(e)}")
                        return None
                    except Exception as e:
                        logger.error(f"Error transcribing chunk {i+1}: {str(e)}")
                        return None
                if not success:
                    logger.error(f"Failed to transcribe chunk {i+1} after {max_retries} attempts")
                    return None
                
        # Reindex entries
        for i, entry in enumerate(all_entries):
            entry["index"] = i + 1
            
        return all_entries
    
    def save_json_transcription(self, entries):
        """
        Save transcription entries in JSON format
        """
        output = {
            "format": "json",
            "entries": entries,
            "metadata": {
                "total_entries": len(entries),
                "total_chunks": max([entry.get("chunk", 0) for entry in entries]) if entries else 0
            }
        }
        
        with open(self.output_item + '.json', "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

#        text = ' '.join([f"[{ d['index']}]{d['text']}" for d in entries])
#        with open(self.output_item + '.script', "w", encoding="utf-8") as f:
#            f.write(text)

        logger.info(f"Saved complete transcription in JSON format to {self.output_item}.json")
        return self.output_item
    
    def cleanup(self):
        """
        Remove temporary files
        """
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up: {str(e)}")
    
    def transcribe(self, audio_path, min_silence_len=500, silence_thresh=-40):
        """
        Main method to transcribe a large audio file
        """
        try:
            # Split audio at silence points
            chunks = self.split_audio_by_size_at_silence(
                audio_path, 
                min_silence_len=min_silence_len, 
                silence_thresh=silence_thresh
            )
            
            # Save chunks to temporary files
            chunk_info = self.save_chunks(chunks)
            
            # Transcribe each chunk
            entries = self.transcribe_chunks(chunk_info)
            if not entries:
                return False
            
            # Save complete transcription in JSON format
            self.save_json_transcription(entries)
            
            return True
        except Exception as e:
            logger.error(f"Error transcribing {str(e)}")
            return False
        
        finally:
            # Clean up temporary files
            self.cleanup()


if __name__ == "__main__":
    audio_path = '/Volumes/Jun SSD/data/audio/S 200322 羅10 6-21 以色列人不信福音7.mp3'
    #    audio_path = '/Volumes/Jun SSD/data/audio/S 190825-GH070077.mp3'

    output = 'data/transcription'
    transcriber = AudioTranscriber(output_item=output)
    transcriber.transcribe(
        audio_path
    )

    logger.info("Transcription complete!")
