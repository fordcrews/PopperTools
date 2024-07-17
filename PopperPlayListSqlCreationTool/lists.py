from flask import Flask, render_template, request, jsonify
import sqlite3
import logging
from collections import Counter

app = Flask(__name__)
db_path = 'C:/vPinball/PinUPSystem/PupDatabase.db'

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ])

# List of valid columns for selection
valid_columns = [
    "GameYear", "Manufact", "NumPlayers", "ThemeColor", "GameType", "TAGS", 
    "Category", "Author", "LaunchCustomVar", "GameTheme", "GameRating", 
    "Special", "CUSTOM2", "CUSTOM3", "GAMEVER", "ALTEXE", "DesignedBy"
]

# Columns that need splitting
split_columns = ["TAGS", "Author", "DesignedBy", "Category", "GameTheme"]

def get_column_values_with_counts(column):
    if column not in valid_columns:
        logging.warning(f"Invalid column: {column}")
        return []
    logging.debug(f"Fetching values for column: {column}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if column in split_columns:
        query = f"SELECT {column} FROM Games WHERE {column} IS NOT NULL AND {column} != ''"
    else:
        query = f"""
        SELECT {column}, COUNT(*) as ItemCount 
        FROM Games 
        WHERE {column} IS NOT NULL AND {column} != ''
        GROUP BY {column} 
        HAVING COUNT(*) > 0
        ORDER BY {column}
        """
    
    logging.debug(f"Executing query: {query}")
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    if column in split_columns:
        values_counter = Counter()
        for row in results:
            items = [item.strip() for item in row[0].split(",")]
            values_counter.update(items)
        
        values = [(tag, count) for tag, count in values_counter.items()]
        values.sort(key=lambda x: x[0])
    else:
        values = results
    
    logging.debug(f"Fetched {len(values)} values for column: {column}")
    return values

def get_games_by_column(column, values):
    if column not in valid_columns:
        logging.warning(f"Invalid column: {column}")
        return []
    logging.debug(f"Fetching games for column: {column} with values: {values}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if column in split_columns:
        query_fragments = [f"{column} LIKE ?" for _ in values]
        query = f"SELECT GameName FROM Games WHERE {' OR '.join(query_fragments)}"
        like_values = [f"%{value}%" for value in values]
        logging.debug(f"Executing query: {query} with values: {like_values}")
        cursor.execute(query, like_values)
    else:
        placeholders = ','.join('?' for _ in values)
        query = f"SELECT GameName FROM Games WHERE {column} IN ({placeholders})"
        logging.debug(f"Executing query: {query} with values: {values}")
        cursor.execute(query, values)
    
    games = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Remove duplicates
    games = list(set(games))
    
    logging.debug(f"Fetched {len(games)} games for column: {column} with values: {values}")
    return games

@app.route('/')
def index():
    return render_template('index.html', columns=valid_columns)

@app.route('/get_values', methods=['POST'])
def get_values():
    column = request.json['column']
    logging.info(f"Received request to get values for column: {column}")
    values = get_column_values_with_counts(column)
    return jsonify(values)

@app.route('/get_games', methods=['POST'])
def get_games():
    column = request.json['column']
    values = request.json['values']
    logging.info(f"Received request to get games for column: {column} with values: {values}")
    games = get_games_by_column(column, values)
    return jsonify(games)

if __name__ == '__main__':
    logging.info("Starting the Flask application")
    app.run(debug=True, host='0.0.0.0', port=5000)
