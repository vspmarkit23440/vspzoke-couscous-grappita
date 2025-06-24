from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "service": "YouTube Transcript API",
        "status": "running",
        "usage": "POST /transcript with {\"video_id\": \"YOUR_VIDEO_ID\"}"
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        # Récupérer les données JSON
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
            
        video_id = data.get('video_id')
        
        if not video_id:
            return jsonify({
                "success": False,
                "error": "video_id is required"
            }), 400
        
        print(f"Attempting to get transcript for video ID: {video_id}")
        
        # Essayer de récupérer la transcription
        transcript_list = None
        language_used = None
        error_message = None
        
        # Essayer d'abord sans spécifier de langue
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            language_used = "auto"
            print(f"Successfully got transcript with auto language")
        except Exception as e:
            error_message = str(e)
            print(f"Failed with auto: {error_message}")
            
            # Essayer avec des langues spécifiques
            for lang in ['en', 'fr', 'es', 'de']:
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                    language_used = lang
                    print(f"Successfully got transcript with language: {lang}")
                    break
                except Exception as e:
                    error_message = str(e)
                    print(f"Failed with {lang}: {error_message}")
                    continue
        
        if not transcript_list:
            print(f"No transcript found for video {video_id}")
            return jsonify({
                "success": False,
                "error": f"No transcript available for this video. Error: {error_message}"
            }), 404
        
        # Joindre tout le texte
        full_text = ' '.join([item['text'] for item in transcript_list])
        
        print(f"Transcript found! Length: {len(full_text)} characters")
        
        return jsonify({
            "success": True,
            "transcript": full_text,
            "length": len(full_text),
            "language": language_used,
            "video_id": video_id
        })
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
