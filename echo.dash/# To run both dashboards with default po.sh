# To run both dashboards with default ports (GUI on 5000, Web on 8080)
./launch_dashboards.py

# To manually start each on specific ports
python3 fix_locale_gui.py --port 5000    # GUI dashboard on port 5000
python3 web_gui.py --port 8080           # Web dashboard on port 8080