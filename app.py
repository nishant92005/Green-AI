"""Green AI – Flask app entry point. Run with: python app.py"""

from backend.main import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
