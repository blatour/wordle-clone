class Rules:
    def __init__(self):
        """Initialize the rules object"""
        self.rules = {
            'overview': 'Wordle is a word guessing game where you try to guess a target word.',
            'gameplay': [
                'Choose a difficulty level that determines word length',
                'You have 6 attempts to guess the word correctly',
                'After each guess, you\'ll get feedback:',
                '- Green: Letter is correct and in the right position',
                '- Yellow: Letter is in the word but in wrong position', 
                '- Gray: Letter is not in the word'
            ],
            'scoring': [
                'Win by guessing the word within 6 attempts',
                'Game ends if word is not guessed after 6 attempts',
                'Statistics track your performance over time'
            ],
            'difficulties': {
                'easy': '4 letters',
                'medium': '5 letters', 
                'hard': '6 letters'
            }
        }

    def get_rules(self) -> dict:
        """Return the game rules"""
        return self.rules
