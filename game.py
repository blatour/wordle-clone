import random
import uuid
from typing import Dict, List, Optional
from database import Database

class Game:
    def __init__(self, difficulty: str):
        """Initialize a new game with specified difficulty"""
        self.db = Database()
        self.game_id = str(uuid.uuid4())
        self.difficulty = difficulty
        self.target_word = self._get_word_for_difficulty()
        self.status = 'active'
        self.guesses = []
        
    def _get_word_for_difficulty(self) -> str:
        """Get a random word based on difficulty level"""
        word_lengths = {
            'easy': 4,
            'medium': 5,
            'hard': 6
        }
        length = word_lengths.get(self.difficulty, 5)
        # This is a simplified word list - in production, use a proper word database
        word_list = ['word', 'game', 'play', 'code', 'test']  # Example words
        return random.choice([w for w in word_list if len(w) == length])

    def initialize(self) -> Dict:
        """Initialize and save the game to database"""
        self.db.save_game(self.game_id, self.difficulty, self.target_word)
        return {
            'game_id': self.game_id,
            'difficulty': self.difficulty,
            'max_attempts': 6,
            'word_length': len(self.target_word)
        }

    @classmethod
    def load_game(cls, game_id: str) -> 'Game':
        """Load an existing game from database"""
        db = Database()
        game_data = db.get_game(game_id)
        if not game_data:
            raise ValueError("Game not found")
            
        game = cls(game_data['difficulty'])
        game.game_id = game_data['game_id']
        game.target_word = game_data['target_word']
        game.status = game_data['status']
        game.guesses = db.get_game_guesses(game_id)
        return game

    def process_guess(self, guess: str) -> Dict:
        """Process a guess and return the result"""
        if self.status != 'active':
            return {'error': 'Game is already finished'}
            
        if len(guess) != len(self.target_word):
            return {'error': 'Invalid guess length'}

        result = self._evaluate_guess(guess)
        
        # Update statistics
        self.db.update_word_stats(guess, guess == self.target_word)
        for i, letter in enumerate(guess):
            self.db.update_letter_stats(letter, i)

        if guess == self.target_word:
            self.status = 'won'
        elif len(self.guesses) >= 5:  # 6 attempts maximum
            self.status = 'lost'

        return result

    def _evaluate_guess(self, guess: str) -> Dict:
        """Evaluate a guess and return the result"""
        result = []
        target_chars = list(self.target_word)
        
        # First pass: mark correct positions
        for i, (guess_char, target_char) in enumerate(zip(guess, self.target_word)):
            if guess_char == target_char:
                result.append('correct')
                target_chars[i] = None
            else:
                result.append('incorrect')

        # Second pass: mark present but misplaced letters
        for i, (guess_char, res) in enumerate(zip(guess, result)):
            if res == 'incorrect' and guess_char in target_chars:
                result[i] = 'present'
                target_chars[target_chars.index(guess_char)] = None

        return {
            'result': result,
            'game_status': self.status
        }
