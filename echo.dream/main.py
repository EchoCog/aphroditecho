from app import app

# Database tables are now created in database.py when init_db is called

# Import the API routes for various subsystems

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
