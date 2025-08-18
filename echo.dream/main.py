from app import app
from database import db

# Database tables are now created in database.py when init_db is called

# Import the API routes for various subsystems
import recursive_distinction_api
import diagnostic_api
import memory_api
import memory_api_visualization

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
