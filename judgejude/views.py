from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import whisper
import logging
import os
import subprocess

# Set the full path to ffmpeg
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"

# Load the Whisper model
model = whisper.load_model("base")

# Set up logging
logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'judgejude/index.html')

@csrf_exempt
def transcribe(request):
    if request.method == 'POST' and request.FILES['audio']:
        try:
            audio_file = request.FILES['audio']
            file_name = default_storage.save(audio_file.name, audio_file)
            file_path = default_storage.path(file_name)

            print(file_name + "/" + file_path)

            # Log the MIME type, file extension, and file size
            mime_type = audio_file.content_type
            file_extension = os.path.splitext(file_name)[1]
            file_size = audio_file.size
            logger.info(f"Received audio file with MIME type: {mime_type}, extension: {file_extension}, size: {file_size} bytes")

            # Print the first few bytes of the file for debugging
            with open(file_path, 'rb') as f:
                file_head = f.read(100)
                logger.info(f"File head: {file_head}")

            # Log additional debug info
            logger.debug(f"File path: {file_path}")
            wav_file_path = file_path + '.wav'
            command = f"ffmpeg -i {file_path} -ac 1 -ar 16000 -f wav {wav_file_path}"
            logger.debug(f"Running command: {command}")

            # Run ffmpeg command and log output
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            logger.debug(f"ffmpeg stdout: {result.stdout}")
            logger.debug(f"ffmpeg stderr: {result.stderr}")

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, command)

            # Check if the WAV file was created successfully
            if not os.path.exists(wav_file_path):
                raise FileNotFoundError(f"WAV file was not created: {wav_file_path}")

            # Transcribe audio using Whisper
            result = model.transcribe(wav_file_path)
            transcription = result['text']

            # Clean up the stored files
            default_storage.delete(file_name)
            if os.path.exists(wav_file_path):
                os.remove(wav_file_path)

            return JsonResponse({'transcription': transcription})
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error: {e.stderr}")
            return JsonResponse({'error': f"ffmpeg error: {e.stderr}"}, status=500)
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)