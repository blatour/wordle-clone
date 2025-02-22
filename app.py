from flask import Flask, render_template, request, jsonify
from database import Database
from game import Game
from rules import Rules
from statistics import Statistics
from user import User
import uuid  # for generating unique game IDs
import json
from pathlib import Path
import random

app = Flask(__name__)
db = Database()

# Initialize or load statistics
def load_statistics():
    try:
        with open('statistics.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'summary': {
                'games_played': 0,
                'games_won': 0,
                'total_attempts': 0
            }
        }

def save_statistics(stats):
    with open('statistics.json', 'w') as f:
        json.dump(stats, f)

class WordDatabase:
    def __init__(self):
        self.words = {
            'easy': set(),
            'normal': set(),
            'hard': set()
        }
        self.used_words = {
            'easy': set(),
            'normal': set(),
            'hard': set()
        }
        self.difficulty_settings = {
            'easy': {'length': 4, 'file': 'words_4.txt'},
            'normal': {'length': 5, 'file': 'words.txt'},
            'hard': {'length': 6, 'file': 'words_6.txt'}
        }
        self.load_all_words()

    def load_all_words(self):
        for difficulty, settings in self.difficulty_settings.items():
            try:
                with open(settings['file'], 'r') as f:
                    # Read all words and filter by length
                    words = {word.strip().upper() for word in f.readlines() 
                            if len(word.strip()) == settings['length']}
                    self.words[difficulty] = words
                print(f"Loaded {len(self.words[difficulty])} words for {difficulty} difficulty")
            except FileNotFoundError:
                print(f"Warning: {settings['file']} not found. Using fallback words.")
                # Add some fallback words for testing
                if difficulty == 'easy':
                    self.words[difficulty] = {'ABLE', 'ACID', 'AGED', 'ALSO', 'AREA', 'ARMY', 'AWAY', 'BABY', 'BACK', 'BALL'}
                elif difficulty == 'normal':
                    self.words[difficulty] = {'ABOUT', 'ABOVE', 'ABUSE', 'ACTOR', 'ACUTE', 'ADMIT', 'ADOPT', 'ADULT', 'AFTER', 'AGAIN'}
                elif difficulty == 'hard':
                    self.words[difficulty] = {'ACCEPT', 'ACTION', 'ACTIVE', 'ACTUAL', 'ADVICE', 'ADVISE', 'AFFECT', 'AGENCY', 'AGENDA', 'AGREED'}

    def get_random_word(self, difficulty='normal'):
        if difficulty not in self.difficulty_settings:
            raise ValueError(f"Invalid difficulty level: {difficulty}")
        
        available_words = [w for w in self.words[difficulty] 
                         if w not in self.used_words[difficulty]]
        
        if not available_words:  # If all words have been used, reset
            self.used_words[difficulty].clear()
            available_words = self.words[difficulty]
        
        if not available_words:  # If no words available for this difficulty
            raise ValueError(f"No words available for difficulty level: {difficulty}")
        
        word = random.choice(available_words)
        self.used_words[difficulty].add(word)
        return word

# Initialize word database
word_db = WordDatabase()

# Game state storage
active_games = {}

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/rules')
def rules():
    """Return the game rules"""
    rules = Rules()
    return jsonify(rules.get_rules())

@app.route('/game', methods=['POST'])
def new_game():
    try:
        data = request.json
        difficulty = data.get('difficulty', 'normal')
        
        if difficulty not in word_db.difficulty_settings:
            return jsonify({
                'error': 'Invalid difficulty level'
            }), 400
        
        game_id = str(uuid.uuid4())
        
        try:
            target_word = word_db.get_random_word(difficulty)
        except ValueError as e:
            return jsonify({
                'error': str(e)
            }), 400
        
        # Store game state
        active_games[game_id] = {
            'word': target_word,
            'attempts': 0,
            'difficulty': difficulty
        }
        
        return jsonify({
            'gameId': game_id,
            'wordLength': len(target_word),
            'difficulty': difficulty,
            'message': 'New game started'
        })
    except Exception as e:
        print(f"Error creating new game: {str(e)}")
        return jsonify({
            'error': 'Failed to create new game'
        }), 500

@app.route('/guess', methods=['POST'])
def make_guess():
    """Process a guess and return the result"""
    try:
        data = request.json
        guess = data.get('guess')
        game_id = data.get('gameId')

        if not guess or not game_id:
            return jsonify({
                'error': 'Missing guess or gameId'
            }), 400

        if game_id not in active_games:
            return jsonify({
                'error': 'Invalid game ID'
            }), 400

        game = active_games[game_id]
        target_word = game['word']
        game['attempts'] = game.get('attempts', 0) + 1
        
        # Generate feedback
        feedback = ""
        correct = guess.upper() == target_word
        
        for i in range(len(guess)):
            if i < len(target_word):
                if guess[i].upper() == target_word[i]:
                    feedback += "O"  # Correct position
                elif guess[i].upper() in target_word:
                    feedback += "?"  # Wrong position
                else:
                    feedback += "X"  # Not in word
            else:
                feedback += "X"

        response_data = {
            'correct': correct,
            'feedback': feedback,
            'guess': guess.upper(),
            'message': 'Congratulations!' if correct else 'Keep trying!',
            'attempts': game['attempts']
        }
        
        # Include the target word if the game is over (win or max attempts)
        if correct or game['attempts'] >= 10:
            response_data['word'] = target_word
            # Clean up the game state
            del active_games[game_id]

        return jsonify(response_data)

    except Exception as e:
        print(f"Error processing guess: {str(e)}")
        return jsonify({
            'error': 'Failed to process guess'
        }), 500

@app.route('/statistics', methods=['GET'])
def get_statistics():
    stats = load_statistics()
    summary = stats['summary']
    win_rate = 0
    avg_attempts = 0
    
    if summary['games_played'] > 0:
        win_rate = round((summary['games_won'] / summary['games_played']) * 100, 1)
    
    if summary['games_won'] > 0:
        avg_attempts = round(summary['total_attempts'] / summary['games_won'], 1)
    
    return jsonify({
        'summary': {
            'games_played': summary['games_played'],
            'win_rate': win_rate,
            'avg_attempts': avg_attempts
        }
    })

@app.route('/statistics/update', methods=['POST'])
def update_statistics():
    try:
        data = request.json
        attempts = data.get('attempts', 0)
        won = data.get('won', False)  # Add won parameter
        
        stats = load_statistics()
        stats['summary']['games_played'] += 1
        
        if won:
            stats['summary']['games_won'] += 1
            stats['summary']['total_attempts'] += attempts
        
        save_statistics(stats)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating statistics: {str(e)}")
        return jsonify({'error': 'Failed to update statistics'}), 500

@app.route('/user/history')
def get_user_history():
    """Return user's game history"""
    user_id = request.args.get('userId')
    user = User(user_id)
    return jsonify(user.get_game_history())

@app.route('/get_possible_words', methods=['POST'])
def get_possible_words():
    try:
        data = request.json
        game_id = data.get('gameId')
        guesses = data.get('guesses', [])
        
        if not game_id:
            return jsonify({'error': 'Missing gameId'}), 400
            
        if game_id not in active_games:
            return jsonify({'error': 'Invalid game ID'}), 400
            
        game = active_games[game_id]
        target_word = game['word']
        difficulty = game['difficulty']
        
        print(f"Processing possible words for game {game_id}")
        print(f"Target word: {target_word}")
        print(f"Received guesses: {guesses}")
        
        # Get all words for the current difficulty
        if difficulty not in word_db.words:
            return jsonify({'error': f'Invalid difficulty level: {difficulty}'}), 400
            
        # Start with all words for this difficulty
        possible_words = set(word_db.words[difficulty])
        print(f"Starting with {len(possible_words)} possible words")
        
        # Filter based on previous guesses
        for guess_data in guesses:
            guess = guess_data['word']
            feedback = guess_data['feedback']
            print(f"Filtering with guess: {guess}, feedback: {feedback}")
            
            before_count = len(possible_words)
            # Filter words that don't match the feedback pattern
            possible_words = {word for word in possible_words 
                            if matches_feedback(word, guess, feedback)}
            
            print(f"After filtering: {len(possible_words)} words remain")
            
        # Calculate letter frequencies for remaining words
        letter_freq = {}
        position_freq = {}
        
        # Initialize position frequency dictionary
        word_length = len(next(iter(possible_words)))
        for pos in range(word_length):
            position_freq[pos] = {}
        
        # Calculate frequencies
        total_words = len(possible_words)
        for word in possible_words:
            # Overall letter frequency
            for letter in word:
                letter_freq[letter] = letter_freq.get(letter, 0) + 1
            
            # Position-specific frequency
            for pos, letter in enumerate(word):
                if letter not in position_freq[pos]:
                    position_freq[pos][letter] = 0
                position_freq[pos][letter] += 1
        
        # Calculate word scores
        word_scores = []
        for word in possible_words:
            score = 0
            seen_letters = set()
            
            # Position-specific scoring
            for pos, letter in enumerate(word):
                pos_probability = position_freq[pos].get(letter, 0) / total_words
                score += pos_probability * 2  # Weight position matches higher
                
                # Letter frequency scoring (only count each letter once)
                if letter not in seen_letters:
                    letter_probability = letter_freq.get(letter, 0) / total_words
                    score += letter_probability
                    seen_letters.add(letter)
            
            # Normalize score
            score = score / (len(word) * 3)  # 3 is max possible score per letter
            word_scores.append((word, score))
        
        # Sort by score descending
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Format results with percentages
        results = [
            {
                'word': word,
                'probability': round(score * 100, 1)  # Convert to percentage
            }
            for word, score in word_scores[:20]  # Limit to top 20
        ]
        
        print(f"Final results: {len(results)} words")
        print(f"Sample of possible words: {[r['word'] for r in results[:5]]}")
        print(f"Target word '{target_word}' is in possible words: {target_word in possible_words}")
        
        return jsonify({
            'possible_words': results,
            'total_count': len(word_scores)
        })
        
    except Exception as e:
        print(f"Error in get_possible_words: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get possible words'}), 500

def matches_feedback(word, guess, feedback):
    """Helper function to check if a word matches the feedback pattern"""
    if len(word) != len(guess):
        return False
    
    word = word.upper()
    guess = guess.upper()
    
    # First pass: Handle correct letters (O)
    for i in range(len(guess)):
        if feedback[i] == 'O':
            if word[i] != guess[i]:
                return False
    
    # Count remaining letters in word (excluding correct positions)
    word_letter_count = {}
    guess_letter_count = {}
    for i in range(len(word)):
        if feedback[i] != 'O':
            word_letter_count[word[i]] = word_letter_count.get(word[i], 0) + 1
            if feedback[i] == '?':
                guess_letter_count[guess[i]] = guess_letter_count.get(guess[i], 0) + 1
    
    # Second pass: Handle wrong positions (?)
    for i in range(len(guess)):
        if feedback[i] == '?':
            # Letter must be in word but not in this position
            if word[i] == guess[i]:  # Can't be in this position
                return False
            if guess[i] not in word_letter_count:  # Must be in word
                return False
            if guess_letter_count.get(guess[i], 0) > word_letter_count.get(guess[i], 0):
                return False
    
    # Third pass: Handle incorrect letters (X)
    for i in range(len(guess)):
        if feedback[i] == 'X':
            # If the letter appears in the word, make sure we've accounted for all instances
            if guess[i] in word_letter_count and word_letter_count[guess[i]] > 0:
                return False
    
    return True

if __name__ == '__main__':
    app.run(debug=True)
