from typing import Dict, List
from database import Database

class User:
    def __init__(self, user_id: str):
        """Initialize user object with database connection"""
        self.user_id = user_id
        self.db = Database()

    def get_game_history(self) -> List[Dict]:
        """Get user's game history"""
        games = self.db.get_user_games(self.user_id)
        
        # Enrich game data with additional info
        for game in games:
            game['guesses'] = self.db.get_game_guesses(game['game_id'])
            
            # Calculate score
            if game['status'] == 'won':
                game['score'] = 6 - len(game['guesses']) + 1
            else:
                game['score'] = 0
                
        return sorted(games, key=lambda x: x['created_at'], reverse=True)