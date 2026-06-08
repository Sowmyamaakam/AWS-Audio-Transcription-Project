import json
import sys
from datetime import timedelta

def format_time(seconds):
       """Convert seconds to HH:MM:SS format"""
       return str(timedelta(seconds=float(seconds))).split('.')[0]

def parse_transcription(json_file):
       """Parse Amazon Transcribe output JSON"""
       
       try:
           with open(json_file, 'r') as f:
               data = json.load(f)
           
           print("\n" + "="*80)
           print("AUDIO TRANSCRIPTION RESULTS")
           print("="*80)
           
           # Job metadata
           job_name = data.get('jobName', 'Unknown')
           status = data.get('status', 'Unknown')
           
           print(f"\nJob Name: {job_name}")
           print(f"Status: {status}")
           
           if 'results' not in data:
               print("\nNo transcription results found.")
               return
           
           # Full transcript
           transcript = data['results']['transcripts'][0]['transcript']
           print(f"\n{'-'*80}")
           print("FULL TRANSCRIPT")
           print(f"{'-'*80}")
           print(transcript)
           print()
           
           # Speaker-separated transcript
           if 'speaker_labels' in data['results']:
               print(f"\n{'-'*80}")
               print("SPEAKER-SEPARATED TRANSCRIPT")
               print(f"{'-'*80}\n")
               
               segments = data['results']['speaker_labels']['segments']
               items = data['results']['items']
               
               for segment in segments:
                   speaker = segment['speaker_label']
                   start = format_time(segment['start_time'])
                   end = format_time(segment['end_time'])
                   
                   # Collect words for this segment
                   words = []
                   for item in items:
                       if 'start_time' in item:
                           item_start = float(item['start_time'])
                           seg_start = float(segment['start_time'])
                           seg_end = float(segment['end_time'])
                           
                           if seg_start <= item_start <= seg_end:
                               words.append(item['alternatives'][0]['content'])
                   
                   text = ' '.join(words)
                   print(f"[{start} - {end}] {speaker}: {text}\n")
           
           # Confidence scores
           print(f"\n{'-'*80}")
           print("CONFIDENCE ANALYSIS")
           print(f"{'-'*80}")
           
           items = data['results']['items']
           confidences = [float(item['alternatives'][0]['confidence']) 
                         for item in items if 'confidence' in item['alternatives'][0]]
           
           if confidences:
               avg_confidence = sum(confidences) / len(confidences)
               print(f"Average Confidence: {avg_confidence:.2%}")
               print(f"Highest Confidence: {max(confidences):.2%}")
               print(f"Lowest Confidence: {min(confidences):.2%}")
               print(f"Total Words: {len(confidences)}")
           
           print("\n" + "="*80 + "\n")
           
       except FileNotFoundError:
           print(f"Error: File '{json_file}' not found")
       except json.JSONDecodeError:
           print(f"Error: Invalid JSON format in '{json_file}'")
       except Exception as e:
           print(f"Error: {str(e)}")

if __name__ == '__main__':
       if len(sys.argv) < 2:
           print("Usage: python parse_transcription.py <json_file>")
           sys.exit(1)
       
       parse_transcription(sys.argv[1])