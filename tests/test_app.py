import pytest
from app import app
from database import Database
from game import Game
from rules import Rules
from statistics import Statistics
from user import User

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test home page returns 200"""
    response = client.get('/')
    assert response.status_code == 200

def test_rules_endpoint(client):
    """Test rules endpoint returns rules data"""
    response = client.get('/rules')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert len(data) > 0

def test_new_game(client):
    """Test creating a new game"""
    response = client.post('/game', json={'difficulty': 'normal'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'gameId' in data
    assert 'wordLength' in data

def test_make_guess(client, mocker):
    """Test making a guess"""
    # Mock game loading and processing
    mock_game = mocker.patch('game.Game')
    mock_game.load_game.return_value.process_guess.return_value = {
        'correct': False,
        'positions': [0, 0, 0, 0, 0]
    }

    response = client.post('/guess', json={
        'gameId': '123',
        'guess': 'TESTS'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'correct' in data
    assert 'positions' in data

def test_statistics(client):
    """Test statistics endpoint"""
    response = client.get('/statistics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'word_stats' in data
    assert 'letter_stats' in data
    assert 'summary' in data

def test_user_history(client):
    """Test user history endpoint"""
    response = client.get('/user/history?userId=test_user')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
