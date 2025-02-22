import sqlite3
from typing import Dict, List, Optional

class Database:
    def __init__(self):
        """Initialize database connection and create tables if they don't exist"""
        self.conn = sqlite3.connect('wordle.db')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        # Games table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                game_id TEXT PRIMARY KEY,
                difficulty TEXT,
                target_word TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Guesses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guesses (
                guess_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                guess TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games (game_id)
            )
        ''')

        # Word statistics table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_stats (
                word TEXT PRIMARY KEY,
                times_used INTEGER DEFAULT 0,
                times_correct INTEGER DEFAULT 0
            )
        ''')

        # Letter statistics table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS letter_stats (
                letter CHAR(1) PRIMARY KEY,
                position INTEGER,
                frequency INTEGER DEFAULT 0
            )
        ''')

        self.conn.commit()

    def save_game(self, game_id: str, difficulty: str, target_word: str) -> None:
        """Save a new game to the database"""
        self.cursor.execute(
            'INSERT INTO games (game_id, difficulty, target_word, status) VALUES (?, ?, ?, ?)',
            (game_id, difficulty, target_word, 'active')
        )
        self.conn.commit()

    def save_guess(self, game_id: str, guess: str, result: Dict) -> None:
        """Save a guess and its result to the database"""
        self.cursor.execute(
            'INSERT INTO guesses (game_id, guess, result) VALUES (?, ?, ?)',
            (game_id, guess, str(result))
        )
        self.conn.commit()

    def get_game(self, game_id: str) -> Optional[Dict]:
        """Retrieve a game by its ID"""
        self.cursor.execute('SELECT * FROM games WHERE game_id = ?', (game_id,))
        game = self.cursor.fetchone()
        if game:
            return {
                'game_id': game[0],
                'difficulty': game[1],
                'target_word': game[2],
                'status': game[3],
                'created_at': game[4]
            }
        return None

    def get_game_guesses(self, game_id: str) -> List[Dict]:
        """Retrieve all guesses for a specific game"""
        self.cursor.execute('SELECT * FROM guesses WHERE game_id = ? ORDER BY created_at', (game_id,))
        guesses = self.cursor.fetchall()
        return [{
            'guess_id': g[0],
            'game_id': g[1],
            'guess': g[2],
            'result': g[3],
            'created_at': g[4]
        } for g in guesses]

    def update_word_stats(self, word: str, correct: bool) -> None:
        """Update statistics for a word"""
        self.cursor.execute('''
            INSERT INTO word_stats (word, times_used, times_correct)
            VALUES (?, 1, ?)
            ON CONFLICT(word) DO UPDATE SET
                times_used = times_used + 1,
                times_correct = times_correct + ?
        ''', (word, int(correct), int(correct)))
        self.conn.commit()

    def update_letter_stats(self, letter: str, position: int) -> None:
        """Update statistics for a letter at a specific position"""
        self.cursor.execute('''
            INSERT INTO letter_stats (letter, position, frequency)
            VALUES (?, ?, 1)
            ON CONFLICT(letter) DO UPDATE SET
                frequency = frequency + 1
        ''', (letter, position))
        self.conn.commit()

    def get_word_stats(self) -> List[Dict]:
        """Retrieve statistics for all words"""
        self.cursor.execute('SELECT * FROM word_stats ORDER BY times_used DESC')
        return [{
            'word': row[0],
            'times_used': row[1],
            'times_correct': row[2]
        } for row in self.cursor.fetchall()]

    def get_letter_stats(self) -> List[Dict]:
        """Retrieve statistics for all letters"""
        self.cursor.execute('SELECT * FROM letter_stats ORDER BY frequency DESC')
        return [{
            'letter': row[0],
            'position': row[1],
            'frequency': row[2]
        } for row in self.cursor.fetchall()]

    def __del__(self):
        """Close database connection when object is destroyed"""
        self.conn.close()
