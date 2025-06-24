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
        data = request.get_json()
        video_id = data.get('video_id')
        
        if not video_id:
            return jsonify({
                "success": False,
                "error": "video_id is required"
            }), 400
        
        # Essaye d'abord en français, puis en anglais
        transcript_list = None
        language_used = None
        
        for lang in ['fr', 'en', 'auto']:
            try:
                if lang == 'auto':
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                else:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                language_used = lang
                break
            except:
                continue
        
        if not transcript_list:
            return jsonify({
                "success": False,
                "error": "No transcript available for this video"
            }), 404
        
        # Joindre tout le texte
        full_text = ' '.join([item['text'] for item in transcript_list])
        
        return jsonify({
            "success": True,
            "transcript": full_text,
            "length": len(full_text),
            "language": language_used,
            "video_id": video_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
