from flask import Flask, request, render_template, g
import sqlite3

DATABASE = 'events.db'
app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = sqlite3.connect(DATABASE)
        g._database = db
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, '_database', None)
    if db:
        db.close()

@app.route("/")
def index():
    query = request.args.get("q", "")
    results = []
    if query:
        q = f"%{query.lower()}%"
        cur = get_db().cursor()
        cur.execute("SELECT title, url FROM events WHERE lower(title) LIKE ? LIMIT 50", (q,))
        results = cur.fetchall()
    return render_template("index.html", results=results, query=query)

if __name__ == "__main__":
    app.run(debug=True)
