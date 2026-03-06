"""Entry point for Green AI. Run with: python main.py or flask --app main run."""

from backend.main import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
