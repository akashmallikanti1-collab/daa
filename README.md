# 🛵 RideShareVCE – Enhanced Edition

A Flask-based ride-sharing web app for Vasavi College of Engineering students,
now featuring **real graph algorithms**, **profile management**, and **live algorithm visualization**.

## 🚀 Features

### Algorithms
| Algorithm | Purpose | Complexity |
|-----------|---------|-----------|
| **Dijkstra's Shortest Path** | Finds the optimal weighted route between areas using a min-heap priority queue | O((V+E) log V) |
| **BFS Sub-path Check** | Verifies requester's route is contained within giver's route | O(V+E) |
| **Greedy Best Match** | Selects highest-overlap candidate among all matches | O(C log C) |

### New in This Version
- 🧠 **Algorithm Visualizer** – Step through Dijkstra, BFS, and the graph view on every result page
- 👤 **Profile Management** – Edit name, phone, bio; change password; view ride stats
- 🗾 **Interactive Graph Canvas** – See the area network with highlighted routes
- 📊 **Match Summary** – Full algorithm trace with complexity analysis

## 🛠️ Setup

```bash
pip install flask
python app.py
```
Open http://localhost:5000

## 📁 Structure

```
rideshare/
├── app.py          # Flask routes (auth, profile, ride, APIs)
├── matching.py     # Dijkstra + BFS + Greedy matching
├── areas.py        # Area graph with GPS coords + weighted edges
├── templates/
│   ├── index.html
│   ├── login.html / signup.html
│   ├── dashboard.html
│   ├── ride.html
│   ├── result.html     ← algorithm visualizer lives here
│   └── profile.html    ← NEW: profile management
└── static/css/style.css
```
