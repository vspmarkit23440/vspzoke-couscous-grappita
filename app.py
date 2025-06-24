from flask import Flask, request, jsonify, abort
from youtube_transcript_api import YouTubeTranscriptApi
import os

app = Flask(__name__)

# Liste des IPs autorisées (depuis variable d'environnement)
# Format: "IP1,IP2,IP3" ou juste "IP1" pour une seule
ALLOWED_IPS = os.environ.get('ALLOWED_IPS', '').split(',')
ALLOWED_IPS = [ip.strip() for ip in ALLOWED_IPS if ip.strip()]

print(f"IPs autorisées: {ALLOWED_IPS}")

@app.before_request
def limit_remote_addr():
    """Vérifie l'IP avant chaque requête"""
    # Skip pour la route de santé
    if request.path == '/health':
        return
    
    # Récupérer l'IP réelle (gère les proxys)
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip:
        # X-Forwarded-For peut contenir plusieurs IPs, on prend la première
        client_ip = client_ip.split(',')[0].strip()
    
    print(f"Requête depuis IP: {client_ip}")
    
    # Si des IPs sont configurées, vérifier
    if ALLOWED_IPS and client_ip not in ALLOWED_IPS:
        print(f"IP non autorisée: {client_ip}")
        return jsonify({
            "error": "Access denied",
            "message": "Your IP is not authorized"
        }), 403

@app.route('/')
def home():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    return jsonify({
        "service": "YouTube Transcript API",
        "status": "running",
        "usage": "POST /transcript with {\"video_id\": \"YOUR_VIDEO_ID\"}",
        "your_ip": client_ip,
        "access": "allowed" if not ALLOWED_IPS or client_ip in ALLOWED_IPS else "would be denied"
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
        
        print(f"Getting transcript for video ID: {video_id}")
        
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

# Route de santé pour Render (sans restriction IP)
@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# Route pour voir son IP (utile pour debug)
@app.route('/my-ip')
def my_ip():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    return jsonify({
        "your_ip": client_ip,
        "headers": dict(request.headers),
        "allowed_ips": ALLOWED_IPS,
        "access": "allowed" if not ALLOWED_IPS or client_ip in ALLOWED_IPS else "denied"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
