from typing import Dict, List
from database import Database

class Statistics:
    def __init__(self):
        """Initialize statistics object with database connection"""
        self.db = Database()

    def get_all_statistics(self) -> Dict:
        """Get all game statistics"""
        return {
            'word_stats': self._get_word_statistics(),
            'letter_stats': self._get_letter_statistics(),
            'summary': self._get_summary_statistics()
        }

    def _get_word_statistics(self) -> List[Dict]:
        """Get statistics about word usage and success rates"""
        word_stats = self.db.get_word_stats()
        
        # Calculate success rate for each word
        for stat in word_stats:
            success_rate = 0
            if stat['times_used'] > 0:
                success_rate = (stat['times_correct'] / stat['times_used']) * 100
            stat['success_rate'] = round(success_rate, 1)
            
        return word_stats

    def _get_letter_statistics(self) -> List[Dict]:
        """Get statistics about letter frequency and positions"""
        return self.db.get_letter_stats()

    def _get_summary_statistics(self) -> Dict:
        """Calculate summary statistics from word and letter data"""
        word_stats = self.db.get_word_stats()
        
        total_games = sum(stat['times_used'] for stat in word_stats)
        total_wins = sum(stat['times_correct'] for stat in word_stats)
        
        win_rate = 0
        if total_games > 0:
            win_rate = (total_wins / total_games) * 100
            
        return {
            'total_games': total_games,
            'total_wins': total_wins,
            'win_rate': round(win_rate, 1)
        }
