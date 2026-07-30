#!/bin/bash
# Live Three.js viewer for the Deskitty rig. Needs a server (ES module imports
# won't load over file://).
cd "$(dirname "$0")"
pkill -f "http.server 8777" 2>/dev/null
python3 -m http.server 8777 >/dev/null 2>&1 &
sleep 1
open "http://localhost:8777/index.html"
echo "serving on http://localhost:8777  (pkill -f 'http.server 8777' to stop)"
