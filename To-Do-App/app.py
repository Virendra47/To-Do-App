from flask import Flask, request, jsonify, g
import sqlite3
import os

app = Flask(__name__, static_folder='.', static_url_path='')
DATABASE = 'todos.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, completed BOOLEAN NOT NULL DEFAULT 0)')
        db.commit()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/todos', methods=['GET'])
def get_todos():
    db = get_db()
    cur = db.execute('SELECT id, title, completed FROM todos ORDER BY id')
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])

@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'title required'}), 400
    title = data['title'].strip()
    if not title:
        return jsonify({'error': 'title cannot be empty'}), 400
    db = get_db()
    cur = db.execute('INSERT INTO todos (title, completed) VALUES (?, ?)', (title, 0))
    db.commit()
    new_id = cur.lastrowid
    row = db.execute('SELECT id, title, completed FROM todos WHERE id = ?', (new_id,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/todos/<int:id>', methods=['PATCH'])
def update_todo(id):
    data = request.get_json()
    if data is None or 'completed' not in data:
        return jsonify({'error': 'completed field required'}), 400
    completed = 1 if data['completed'] else 0
    db = get_db()
    db.execute('UPDATE todos SET completed = ? WHERE id = ?', (completed, id))
    db.commit()
    row = db.execute('SELECT id, title, completed FROM todos WHERE id = ?', (id,)).fetchone()
    if row is None:
        return jsonify({'error': 'todo not found'}), 404
    return jsonify(dict(row))

@app.route('/api/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    db = get_db()
    db.execute('DELETE FROM todos WHERE id = ?', (id,))
    db.commit()
    return jsonify({'message': 'deleted'}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)