from test_api import create_users, create_game, join_game
import requests
# Script to create a game with 3 players and a game master


if __name__ == '__main__':
    users = create_users(4)
    game = create_game()
    for user in users[1:]:
        join_game(game, user)
