from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)
db_path = 'C:/vPinball/PinUPSystem/PupDatabase.db'

# List of valid columns for selection
valid_columns = [
    "GameYear", "Manufact", "NumPlayers", "ThemeColor", "GameType", "TAGS", 
    "Category", "Author", "LaunchCustomVar", "GameTheme", "GameRating", 
    "Special", "CUSTOM2", "CUSTOM3", "GAMEVER", "ALTEXE", "DesignedBy"
]

def get_column_values_with_counts(column):
    if column not in valid_columns:
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"""
    SELECT {column}, COUNT(*) as ItemCount 
    FROM Games 
    WHERE {column} IS NOT NULL AND {column} != ''
    GROUP BY {column} 
    HAVING COUNT(*) > 0
    ORDER BY {column}
    """
    cursor.execute(query)
    values = cursor.fetchall()
    conn.close()
    return values

def get_games_by_column(column, values):
    if column not in valid_columns:
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in values)
    query = f"""
    SELECT GameName 
    FROM Games 
    WHERE {column} IN ({placeholders})
    """
    cursor.execute(query, values)
    games = [row[0] for row in cursor.fetchall()]
    conn.close()
    return games

@app.route('/')
def index():
    return render_template('index.html', columns=valid_columns)

@app.route('/get_values', methods=['POST'])
def get_values():
    column = request.json['column']
    values = get_column_values_with_counts(column)
    return jsonify(values)

@app.route('/get_games', methods=['POST'])
def get_games():
    column = request.json['column']
    values = request.json['values']
    games = get_games_by_column(column, values)
    return jsonify(games)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
