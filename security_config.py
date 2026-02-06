from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for all domains
CORS(app)

# Rate Limiting configuration
limiter = Limiter(app, key_func=lambda: request.remote_addr)

# Example: Limit to 100 requests per minute
@limiter.limit("100 per minute")
def some_route():
    return "This is a rate-limited route"

if __name__ == "__main__":
    app.run(ssl_context=('path/to/cert.pem', 'path/to/key.pem'))  # HTTPS setup