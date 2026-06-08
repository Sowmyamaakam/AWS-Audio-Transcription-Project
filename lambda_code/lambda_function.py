import json
import boto3
import base64
import uuid
from datetime import datetime

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')

# CHANGE THESE TO YOUR BUCKET NAMES!
INPUT_BUCKET = 'audio-input-sowmya-98765 '
OUTPUT_BUCKET = 'audio-output-sowmya-98765'

def lambda_handler(event, context):
    """
    Handle API Gateway requests for audio transcription
    """
    
    # Enable CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    }
    
    # Handle OPTIONS request (CORS preflight)
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    # Handle POST - Upload audio
    if event['httpMethod'] == 'POST' and event['path'] == '/upload':
        return handle_upload(event, headers)
    
    # Handle GET - Check status
    if event['httpMethod'] == 'GET' and event['path'] == '/status':
        return handle_status(event, headers)
    
    # Handle GET - Get result
    if event['httpMethod'] == 'GET' and event['path'] == '/result':
        return handle_result(event, headers)
    
    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({'error': 'Not found'})
    }

def handle_upload(event, headers):
    """Handle audio file upload"""
    try:
        # Parse request body
        body = json.loads(event['body'])
        
        # Get base64 encoded audio data
        audio_data = body['audioData']
        filename = body['filename']
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data.split(',')[1] if ',' in audio_data else audio_data)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        file_extension = filename.split('.')[-1]
        s3_key = f"{timestamp}-{unique_id}.{file_extension}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=INPUT_BUCKET,
            Key=s3_key,
            Body=audio_bytes,
            ContentType=f'audio/{file_extension}'
        )
        
        print(f"Uploaded file: {s3_key}")
        
        # Start transcription job
        job_name = f"web-transcribe-{timestamp}-{unique_id}"
        
        media_format_map = {
            'mp3': 'mp3', 'wav': 'wav', 'm4a': 'mp4',
            'mp4': 'mp4', 'flac': 'flac', 'ogg': 'ogg'
        }
        media_format = media_format_map.get(file_extension.lower(), 'mp3')
        
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{INPUT_BUCKET}/{s3_key}'},
            MediaFormat=media_format,
            LanguageCode='en-US',
            OutputBucketName=OUTPUT_BUCKET,
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10
            }
        )
        
        print(f"Started job: {job_name}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Upload successful',
                'jobName': job_name,
                's3Key': s3_key
            })
        }
        
    except Exception as e:
        print(f"Error in upload: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_status(event, headers):
    """Check transcription job status"""
    try:
        # Get job name from query parameters
        job_name = event['queryStringParameters']['jobName']
        
        # Get job status
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        
        job = response['TranscriptionJob']
        status = job['TranscriptionJobStatus']
        
        result = {
            'status': status,
            'jobName': job_name
        }
        
        # If completed, include output location
        if status == 'COMPLETED':
            result['outputUri'] = job['Transcript']['TranscriptFileUri']
        elif status == 'FAILED':
            result['failureReason'] = job.get('FailureReason', 'Unknown error')
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error checking status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_result(event, headers):
    """Get transcription result"""
    try:
        # Get job name from query parameters
        job_name = event['queryStringParameters']['jobName']
        
        # Get result from S3
        result_key = f"{job_name}.json"
        
        response = s3_client.get_object(
            Bucket=OUTPUT_BUCKET,
            Key=result_key
        )
        
        # Parse transcription result
        result_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Extract transcript
        transcript = result_data['results']['transcripts'][0]['transcript']
        
        # Extract speaker segments if available
        speakers = []
        if 'speaker_labels' in result_data['results']:
            segments = result_data['results']['speaker_labels']['segments']
            items = result_data['results']['items']
            
            for segment in segments:
                speaker = segment['speaker_label']
                start_time = segment['start_time']
                end_time = segment['end_time']
                
                # Get words for this segment
                words = []
                for item in items:
                    if 'start_time' in item:
                        if float(segment['start_time']) <= float(item['start_time']) <= float(segment['end_time']):
                            words.append(item['alternatives'][0]['content'])
                
                speakers.append({
                    'speaker': speaker,
                    'startTime': start_time,
                    'endTime': end_time,
                    'text': ' '.join(words)
                })
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'transcript': transcript,
                'speakers': speakers,
                'jobName': job_name
            })
        }
        
    except Exception as e:
        print(f"Error getting result: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }