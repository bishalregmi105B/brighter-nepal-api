"""
Entry point — run with:
  python run.py          (dev mode, port 5000)
  flask run --port 5000  (alternative)
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
