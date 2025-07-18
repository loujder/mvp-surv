from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import threading
import json
import math
import eventlet
import traceback
import random
import sys

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://auth_user:auth_password@postgres:5432/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

lobby_timer = 10
lobby_timer_running = False
lobby_timer_lock = threading.Lock()

game_timer = 15
game_timer_running = False
game_timer_lock = threading.Lock()
game_session_id = None

choice_timer = 10
choice_timer_running = False
choice_timer_lock = threading.Lock()
choice_session_id = None

@app.route('/api/data')
def get_data():
    return jsonify({'message': "hello world"})

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True, nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    balance = db.Column(db.Integer, default=10)

    def __repr__(self):
        return f'<User {self.nickname}>'

class Lobby(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lobby_id = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.String(80), nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_observer = db.Column(db.Boolean, default=False)
    is_ready = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'lobby_id': self.lobby_id,
            'user_id': self.user_id,
            'nickname': self.nickname,
            'joined_at': self.joined_at.isoformat(),
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'is_observer': self.is_observer
        }

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lobby_id = db.Column(db.String(80), nullable=False, unique=True)
    status = db.Column(db.String(20), default='waiting')
    current_round = db.Column(db.Integer, default=1)
    total_rounds = db.Column(db.Integer, default=1)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)
    winner_id = db.Column(db.String(80))
    initial_bank = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'lobby_id': self.lobby_id,
            'status': self.status,
            'current_round': self.current_round,
            'total_rounds': self.total_rounds,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'winner_id': self.winner_id,
            'initial_bank': self.initial_bank
        }

class GameRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    eliminated_players = db.Column(db.Text)
    bank = db.Column(db.Integer, default=0)
    players_choice = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'game_session_id': self.game_session_id,
            'round_number': self.round_number,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'eliminated_players': self.eliminated_players,
            'bank': self.bank,
            'players_choice': self.players_choice
        }

class PlayerChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.String(80), nullable=False)
    choice = db.Column(db.String(10), nullable=False)
    coins_earned = db.Column(db.Integer, default=0)
    made_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'game_session_id': self.game_session_id,
            'round_number': self.round_number,
            'user_id': self.user_id,
            'choice': self.choice,
            'coins_earned': self.coins_earned,
            'made_at': self.made_at.isoformat()
        }

class PlayerGameStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    user_id = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default='active')
    eliminated_in_round = db.Column(db.Integer, nullable=True)
    quit_in_round = db.Column(db.Integer, nullable=True)
    total_coins_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'game_session_id': self.game_session_id,
            'user_id': self.user_id,
            'status': self.status,
            'eliminated_in_round': self.eliminated_in_round,
            'quit_in_round': self.quit_in_round,
            'total_coins_earned': self.total_coins_earned,
            'created_at': self.created_at.isoformat()
        }

@app.before_request
def create_tables():
    try:
        db.create_all()
        print("Database tables created/verified successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")

def clear_lobby_on_startup():
    try:
        with app.app_context():
            Lobby.query.update({'is_active': False})
            db.session.commit()
            print("Lobby cleared on startup")
    except Exception as e:
        print(f"Error clearing lobby on startup: {e}")

try:
    clear_lobby_on_startup()
    print("Lobby cleared on startup successfully")
except Exception as e:
    print(f"Error clearing lobby on startup: {str(e)}")
    print(f"Full traceback: {traceback.format_exc()}")

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    user_id = data.get('user_id')
    nickname = data.get('nickname')

    if not user_id or not nickname:
        return jsonify({'error': 'Missing user_id or nickname'}), 400

    if User.query.filter_by(user_id=user_id).first():
        return jsonify({'error': 'User ID already exists'}), 400

    is_admin = user_id == 'Loujder'

    user = User(user_id=user_id, nickname=nickname, balance=10)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'is_admin': is_admin
    }), 201

@app.route('/api/admin/assign', methods=['POST'])
def assign_admin():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    lobby_entry = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
    if lobby_entry:
        lobby_entry.is_admin = True
        db.session.commit()

    return jsonify({
        'message': f'User {user_id} assigned as admin',
        'user_id': user_id
    }), 200

@app.route('/api/admin/check', methods=['GET'])
def check_admin_status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    is_admin = user_id == 'Loujder'

    return jsonify({
        'user_id': user_id,
        'is_admin': is_admin
    }), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'message': 'Login successful',
        'nickname': user.nickname,
        'user_id': user.user_id,
        'balance': user.balance
    }), 200

@app.route('/api/user', methods=['GET'])
def get_user():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user_id': user.user_id,
        'nickname': user.nickname,
        'balance': user.balance
    }), 200

@app.route('/api/coins/deduct', methods=['POST'])
def deduct_coins():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount', 1)

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user_id == 'Loujder':
        return jsonify({
            'message': 'Admin user - no coins deducted',
            'balance': user.balance,
            'deducted': 0
        }), 200

    if user.balance < amount:
        return jsonify({'error': 'Insufficient balance', 'balance': user.balance}), 400

    user.balance -= amount
    db.session.commit()

    return jsonify({
        'message': 'Coins deducted successfully',
        'balance': user.balance,
        'deducted': amount
    }), 200

@app.route('/api/coins/add', methods=['POST'])
def add_coins():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount', 1)

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.balance += amount
    db.session.commit()

    return jsonify({
        'message': 'Coins added successfully',
        'balance': user.balance,
        'added': amount
    }), 200

@app.route('/api/coins/balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'balance': user.balance
    }), 200

@app.route('/api/lobby/join', methods=['POST'])
def join_lobby():
    data = request.json
    user_id = data.get('user_id')
    lobby_id = data.get('lobby_id')

    if not user_id or not lobby_id:
        return jsonify({'error': 'Missing user_id or lobby_id'}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    existing_lobby_entry = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
    if existing_lobby_entry:
        existing_lobby_entry.is_active = False
        db.session.commit()

    is_admin = user_id == 'Loujder'

    lobby_entry = Lobby(
        user_id=user_id,
        nickname=user.nickname,
        lobby_id=lobby_id
    )
    db.session.add(lobby_entry)
    db.session.commit()

    return jsonify({
        'message': 'Successfully joined lobby',
        'user_id': user_id,
        'nickname': user.nickname,
        'lobby_id': lobby_id,
        'is_admin': is_admin,
        'is_observer': is_admin
    }), 200

@app.route('/api/lobby/leave', methods=['POST'])
def leave_lobby():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    lobby_entry = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
    if not lobby_entry:
        return jsonify({'error': 'User not in lobby'}), 404

    current_game = GameSession.query.filter_by(status='playing').first()

    if current_game and user_id != 'Loujder':
        player_status = PlayerGameStatus.query.filter_by(game_session_id=current_game.id, user_id=user_id, status='active').first()
        if player_status:
            player_status.status = 'quit'
            player_status.quit_in_round = current_game.current_round
            db.session.commit()
            statuses = PlayerGameStatus.query.filter_by(game_session_id=current_game.id).all()
            socketio.emit('player_status_update', {
                'statuses': [s.to_dict() for s in statuses]
            })

    if user_id != 'Loujder' and lobby_entry.is_ready:
        return jsonify({'error': 'Cannot leave lobby when ready for game'}), 400

    lobby_entry.is_active = False
    db.session.commit()

    return jsonify({
        'message': 'Successfully left lobby',
        'user_id': user_id
    }), 200

@app.route('/api/lobby/ready', methods=['POST'])
def set_player_ready():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    lobby_entry = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
    if not lobby_entry:
        return jsonify({'error': 'User not in lobby'}), 404

    if user_id == 'Loujder':
        return jsonify({'error': 'Admin cannot be ready for game'}), 400

    lobby_entry.is_ready = True
    db.session.commit()

    return jsonify({
        'message': 'Player is ready for game',
        'user_id': user_id
    }), 200

@app.route('/api/lobby/unready', methods=['POST'])
def set_player_unready():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    lobby_entry = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
    if not lobby_entry:
        return jsonify({'error': 'User not in lobby'}), 404

    if user_id == 'Loujder':
        return jsonify({'error': 'Admin cannot be ready for game'}), 400

    lobby_entry.is_ready = False
    db.session.commit()

    return jsonify({
        'message': 'Player is no longer ready for game',
        'user_id': user_id
    }), 200

@app.route('/api/lobby/reset-ready', methods=['POST'])
def reset_player_ready():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    try:
        player = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
        if player:
            player.is_ready = False
            db.session.commit()
            return jsonify({'message': 'Player ready status reset'}), 200
        else:
            return jsonify({'error': 'Player not found in lobby'}), 404
    except Exception as e:
        return jsonify({'error': f'Error resetting player ready status: {str(e)}'}), 500

@app.route('/api/lobby/ready', methods=['GET'])
def check_player_ready():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    try:
        player = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
        if player:
            return jsonify({'is_ready': player.is_ready}), 200
        else:
            return jsonify({'is_ready': False}), 200
    except Exception as e:
        return jsonify({'error': f'Error checking player ready status: {str(e)}'}), 500

@app.route('/api/lobby/players', methods=['GET'])
def get_lobby_players():
    active_players = Lobby.query.filter_by(is_active=True).order_by(Lobby.joined_at.asc()).all()

    current_game = GameSession.query.filter_by(status='playing').first()
    game_session_id = current_game.id if current_game else None

    player_statuses = {}
    if game_session_id:
        for status in PlayerGameStatus.query.filter_by(game_session_id=game_session_id).all():
            player_statuses[status.user_id] = status

    players = []
    for player in active_players:
        if player.user_id == 'Loujder':
            continue
        player_data = player.to_dict()
        player_data['is_admin'] = False
        player_data['is_joined'] = True
        player_data['is_ready'] = player.is_ready
        player_data['is_observer'] = player.is_observer
        player_data['is_eliminated'] = False
        player_data['is_in_game'] = False
        player_data['is_winner'] = False

        if current_game:
            status = player_statuses.get(player.user_id)
            if status:
                if status.status == 'eliminated':
                    player_data['is_eliminated'] = True
                elif status.status == 'winner':
                    player_data['is_winner'] = True
                elif status.status == 'active':
                    player_data['is_in_game'] = True
                elif status.status == 'quit':
                    player_data['is_eliminated'] = True
            else:
                pass
        players.append(player_data)
    return jsonify({
        'players': players,
        'count': len(players)
    }), 200

@app.route('/api/admin/lobby/players', methods=['GET'])
def get_admin_lobby_players():
    lobby_id = request.args.get('lobby_id')
    if lobby_id:
        active_players = Lobby.query.filter_by(is_active=True, lobby_id=lobby_id).order_by(Lobby.joined_at.asc()).all()
    else:
        active_players = Lobby.query.filter_by(is_active=True).order_by(Lobby.joined_at.asc()).all()
    current_game = GameSession.query.filter_by(status='playing').first()
    game_session_id = current_game.id if current_game else None
    player_statuses = {}
    if game_session_id:
        for status in PlayerGameStatus.query.filter_by(game_session_id=game_session_id).all():
            player_statuses[status.user_id] = status
    players = []
    for player in active_players:
        player_data = player.to_dict()
        player_data['is_admin'] = player.user_id == 'Loujder'
        player_data['is_joined'] = True
        player_data['is_ready'] = player.is_ready
        player_data['is_observer'] = player.is_observer
        player_data['is_eliminated'] = False
        player_data['is_in_game'] = False
        player_data['is_winner'] = False
        if current_game:
            status = player_statuses.get(player.user_id)
            if status:
                if status.status == 'eliminated':
                    player_data['is_eliminated'] = True
                elif status.status == 'winner':
                    player_data['is_winner'] = True
                elif status.status == 'active':
                    player_data['is_in_game'] = True
                elif status.status == 'quit':
                    player_data['is_eliminated'] = True
        players.append(player_data)
    return jsonify({
        'players': players,
        'count': len(players),
        'lobby_id': lobby_id
    }), 200

@app.route('/api/admin/lobby/<lobby_id>/join', methods=['POST'])
def admin_join_specific_lobby(lobby_id):
    data = request.json
    user_id = data.get('user_id')

    if not user_id or user_id != 'Loujder':
        return jsonify({'error': 'Only admin can use this endpoint'}), 403

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    existing_entries = Lobby.query.filter_by(user_id=user_id, is_active=True).all()
    for entry in existing_entries:
        entry.is_active = False

    lobby_entry = Lobby(
        user_id=user_id,
        nickname=user.nickname,
        lobby_id=lobby_id,
        is_admin=True,
        is_observer=True
    )
    db.session.add(lobby_entry)
    db.session.commit()

    return jsonify({
        'message': 'Admin successfully joined specific lobby',
        'user_id': user_id,
        'nickname': user.nickname,
        'lobby_id': lobby_id,
        'is_admin': True,
        'is_observer': True
    }), 200

@app.route('/api/lobby/clear', methods=['POST'])
def clear_lobby():
    Lobby.query.delete()
    GameSession.query.delete()
    db.session.commit()
    return jsonify({'message': 'Lobby and game sessions cleared'}), 200

@app.route('/api/admin/give-coins-to-all', methods=['POST'])
def give_coins_to_all():
    try:
        all_users = User.query.all()
        updated_count = 0

        for user in all_users:
            user.balance = 10
            updated_count += 1

        db.session.commit()

        return jsonify({
            'message': f'Successfully updated balance for {updated_count} users',
            'updated_count': updated_count,
            'new_balance': 10
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Error updating balances: {str(e)}'
        }), 500

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    try:
        users = User.query.all()
        user_list = []

        for user in users:
            user_list.append({
                'user_id': user.user_id,
                'nickname': user.nickname,
                'balance': user.balance
            })

        return jsonify({
            'users': user_list,
            'total_count': len(user_list)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error getting users: {str(e)}'
        }), 500

@socketio.on('join_lobby')
def ws_join_lobby(data):
    user_id = data.get('user_id')
    lobby_id = data.get('lobby_id')
    if not user_id or not lobby_id:
        return
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return
    existing = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
    if not existing:
        lobby_entry = Lobby(user_id=user_id, nickname=user.nickname, lobby_id=lobby_id)
        db.session.add(lobby_entry)
        db.session.commit()
    emit_lobby_update()

@socketio.on('leave_lobby')
def ws_leave_lobby(data):
    user_id = data.get('user_id')
    if not user_id:
        return
    lobby_entry = Lobby.query.filter_by(user_id=user_id, is_active=True).first()
    if lobby_entry:
        lobby_entry.is_active = False
        db.session.commit()
    emit_lobby_update()

@socketio.on('request_lobby')
def ws_request_lobby():
    emit_lobby_update()

@socketio.on('request_timer')
def ws_request_timer():
    emit('timer_update', {'time': lobby_timer})

@socketio.on('start_game')
def ws_start_game(data):
    lobby_id = data.get('lobby_id')
    if not lobby_id:
        return

    with app.app_context():
        all_lobby_players = Lobby.query.filter_by(is_active=True, is_admin=False, is_observer=False).all()
        for p in all_lobby_players:
            pass
        ready_players = Lobby.query.filter_by(is_active=True, is_admin=False, is_observer=False, is_ready=True).all()
        if not ready_players:
            return jsonify({'error': 'No ready players in lobby'}), 400
        initial_bank = len(ready_players)
        game_session = GameSession(
            lobby_id=lobby_id,
            status='playing',
            total_rounds=calculate_total_rounds(len(ready_players)),
            initial_bank=initial_bank
        )
        db.session.add(game_session)
        db.session.commit()
        game_session_data = game_session.to_dict()
    return jsonify({
        'message': 'Game started successfully',
        'game_session': game_session_data
    }), 200

def emit_lobby_update():
    try:
        active_players = Lobby.query.filter_by(is_active=True).order_by(Lobby.joined_at.asc()).all()
        players = [player.to_dict() for player in active_players]
        socketio.emit('lobby_update', {'players': players, 'count': len(players)})
    except Exception as e:
        pass

def emit_admin_lobby_update():
    try:
        lobbies = db.session.query(Lobby.lobby_id).distinct().all()
        lobby_list = []

        for (lobby_id,) in lobbies:
            active_players = Lobby.query.filter_by(
                lobby_id=lobby_id,
                is_active=True
            ).count()

            game_session = GameSession.query.filter_by(lobby_id=lobby_id).first()
            status = game_session.status if game_session else 'waiting'

            lobby_list.append({
                'lobby_id': lobby_id,
                'player_count': active_players,
                'status': status
            })

        socketio.emit('admin_lobby_update', {
            'lobbies': lobby_list,
            'total_count': len(lobby_list)
        })
    except Exception as e:
        print(f"Error in emit_admin_lobby_update: {e}")

def start_game_timer(game_session_id_param):
    global game_timer, game_timer_running, game_session_id
    print(f"=== STARTING GAME TIMER (NEW ROUND SYSTEM) ===", file=sys.stderr)
    print(f"Session ID: {game_session_id_param}", file=sys.stderr)

    try:
        with app.app_context():
            game_session = GameSession.query.get(game_session_id_param)
            if not game_session:
                print("Game session not found", file=sys.stderr)
                return

            start_round_timer(game_session_id_param, game_session.current_round)

    except Exception as e:
        print(f"Error in start_game_timer: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def start_round_timer(game_session_id_param, round_number):
    global game_timer, game_timer_running, game_session_id
    print(f"=== STARTING ROUND {round_number} TIMER ===", file=sys.stderr)

    try:
        with game_timer_lock:
            game_timer = 15  # 15 секунд на раунд
            game_timer_running = True
            game_session_id = game_session_id_param
            print(f"Round {round_number} timer set to {game_timer} seconds", file=sys.stderr)

        socketio.emit('game_timer_start', {
            'time': game_timer,
            'game_session_id': game_session_id,
            'round_number': round_number
        })
        print(f"Round {round_number} timer start command emitted to all players", file=sys.stderr)

        def timer_thread():
            global game_timer, game_timer_running
            print(f"Round {round_number} timer thread started", file=sys.stderr)
            while True:
                eventlet.sleep(1)
                with game_timer_lock:
                    if game_timer_running and game_timer > 0:
                        game_timer -= 1
                        socketio.emit('game_timer_update', {
                            'time': game_timer,
                            'game_session_id': game_session_id,
                            'round_number': round_number
                        })
                        print(f"Round {round_number} timer: {game_timer} seconds left", file=sys.stderr)
                    if game_timer == 0:
                        game_timer_running = False
                        print(f"=== ROUND {round_number} TIMER FINISHED ===", file=sys.stderr)
                        finish_round(game_session_id, round_number)
                        break
        eventlet.spawn(timer_thread)
        print(f"Round {round_number} timer thread spawned successfully", file=sys.stderr)

    except Exception as e:
        print(f"Error in start_round_timer: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def finish_round(game_session_id_param, round_number):
    try:
        with app.app_context():
            print(f"=== FINISHING ROUND {round_number} ===", file=sys.stderr)

            remaining_players = eliminate_players_in_round(game_session_id_param, round_number)

            eliminated_players = PlayerGameStatus.query.filter_by(
                game_session_id=game_session_id_param,
                eliminated_in_round=round_number
            ).all()

            print(f"Eliminated players from database: {[p.user_id for p in eliminated_players]}", file=sys.stderr)

            statuses = PlayerGameStatus.query.filter_by(game_session_id=game_session_id_param).all()
            socketio.emit('player_status_update', {
                'statuses': [s.to_dict() for s in statuses]
            })
            print(f"Player status update sent after round {round_number}", file=sys.stderr)

            game_session = GameSession.query.get(game_session_id_param)
            if not game_session:
                print("Game session not found", file=sys.stderr)
                return

            if not remaining_players or len(remaining_players) == 0:
                if len(active_players) > 0:
                    winner_statuses = PlayerGameStatus.query.filter(
                        PlayerGameStatus.game_session_id == game_session_id_param,
                        PlayerGameStatus.user_id.in_([p.user_id for p in active_players])
                    ).all()
                    finish_game_with_split_bank(game_session_id_param, winner_statuses)
                else:
                    finish_game_without_winner(game_session_id_param)
            elif len(remaining_players) == 1:
                winner = remaining_players[0]
                finish_game_with_winner(game_session_id_param, winner.user_id)
            else:
                start_choice_phase(game_session_id_param, round_number, remaining_players)

    except Exception as e:
        print(f"Error in finish_round: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def start_choice_phase(game_session_id_param, round_number, active_players):
    try:
        print(f"=== STARTING CHOICE PHASE FOR ROUND {round_number} ===", file=sys.stderr)
        print(f"Active players: {len(active_players)}", file=sys.stderr)

        choice_data = {
            'game_session_id': game_session_id_param,
            'round_number': round_number,
            'active_players': [p.user_id for p in active_players],
            'choice_timeout': 10  # 10 секунд на выбор
        }

        socketio.emit('choice_phase_started', choice_data)
        print("Choice phase started event sent", file=sys.stderr)

        start_choice_timer(game_session_id_param, round_number, active_players)

    except Exception as e:
        print(f"Error in start_choice_phase: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def start_choice_timer(game_session_id_param, round_number, active_players):
    global choice_timer, choice_timer_running, choice_session_id

    try:
        with choice_timer_lock:
            choice_timer = 10  # 10 секунд на выбор
            choice_timer_running = True
            choice_session_id = game_session_id_param
            print(f"Choice timer set to {choice_timer} seconds", file=sys.stderr)

        socketio.emit('choice_timer_start', {
            'time': choice_timer,
            'game_session_id': game_session_id_param,
            'round_number': round_number
        })

        def choice_timer_thread():
            global choice_timer, choice_timer_running
            print("Choice timer thread started", file=sys.stderr)
            while True:
                eventlet.sleep(1)
                with choice_timer_lock:
                    if choice_timer_running and choice_timer > 0:
                        choice_timer -= 1
                        socketio.emit('choice_timer_update', {
                            'time': choice_timer,
                            'game_session_id': game_session_id_param,
                            'round_number': round_number
                        })
                        print(f"Choice timer: {choice_timer} seconds left", file=sys.stderr)
                    if choice_timer == 0:
                        choice_timer_running = False
                        print("=== CHOICE TIMER FINISHED ===", file=sys.stderr)
                        finish_choice_phase(game_session_id_param, round_number, active_players)
                        break
        eventlet.spawn(choice_timer_thread)
        print("Choice timer thread spawned successfully", file=sys.stderr)

    except Exception as e:
        print(f"Error in start_choice_timer: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def finish_choice_phase(game_session_id_param, round_number, active_players):
    try:
        with app.app_context():
            print(f"=== FINISHING CHOICE PHASE FOR ROUND {round_number} ===", file=sys.stderr)
            choices = PlayerChoice.query.filter_by(
                game_session_id=game_session_id_param,
                round_number=round_number
            ).all()
            staying_players = []
            leave_votes = 0
            for player_status in active_players:
                choice = next((c for c in choices if c.user_id == player_status.user_id), None)
                if choice and choice.choice == 'stay':
                    staying_players.append(player_status)
                elif choice and choice.choice == 'leave':
                    leave_votes += 1
                    player_status.status = 'quit'
                    player_status.quit_in_round = round_number
                    db.session.commit()
                    print(f"Player {player_status.user_id} quit in round {round_number}", file=sys.stderr)
            statuses = PlayerGameStatus.query.filter_by(game_session_id=game_session_id_param).all()
            socketio.emit('player_status_update', {
                'statuses': [s.to_dict() for s in statuses]
            })
            print(f"Player status update sent after choice phase {round_number}", file=sys.stderr)
            if len(staying_players) == 0:
                if len(active_players) > 0:
                    winner_statuses = PlayerGameStatus.query.filter(
                        PlayerGameStatus.game_session_id == game_session_id_param,
                        PlayerGameStatus.user_id.in_([p.user_id for p in active_players])
                    ).all()
                    finish_game_with_split_bank(game_session_id_param, winner_statuses)
                else:
                    finish_game_without_winner(game_session_id_param)
            elif len(staying_players) == 1:
                winner = staying_players[0]
                finish_game_with_winner(game_session_id_param, winner.user_id)
            else:
                total_votes = len(staying_players) + leave_votes
                if leave_votes >= math.ceil(total_votes / 2):
                    winner_statuses = PlayerGameStatus.query.filter(
                        PlayerGameStatus.game_session_id == game_session_id_param,
                        PlayerGameStatus.user_id.in_([p.user_id for p in staying_players])
                    ).all()
                    finish_game_with_split_bank(game_session_id_param, winner_statuses)
                else:
                    start_next_round(game_session_id_param, round_number, staying_players)
    except Exception as e:
        print(f"Error in finish_choice_phase: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def start_next_round(game_session_id_param, current_round, active_players):
    try:
        with app.app_context():
            next_round = current_round + 1
            print(f"=== STARTING NEXT ROUND {next_round} ===", file=sys.stderr)

            game_session = GameSession.query.get(game_session_id_param)
            if game_session:
                game_session.current_round = next_round
                db.session.commit()

                round_update_data = {
                    'game_session_id': game_session_id_param,
                    'current_round': next_round,
                    'total_rounds': game_session.total_rounds,
                    'active_players': [p.user_id for p in active_players]
                }
                socketio.emit('round_updated', round_update_data)
                print(f"Round updated event sent: round {next_round}", file=sys.stderr)

            start_round_timer(game_session_id_param, next_round)

    except Exception as e:
        print(f"Error in start_next_round: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def finish_game_with_winner(game_session_id_param, winner_id):
    try:
        with app.app_context():
            print(f"=== GAME FINISHED WITH WINNER: {winner_id} ===", file=sys.stderr)

            game_session = GameSession.query.get(game_session_id_param)
            if not game_session:
                print("Game session not found", file=sys.stderr)
                return

            winner_status = PlayerGameStatus.query.filter_by(
                game_session_id=game_session_id_param,
                user_id=winner_id
            ).first()

            if winner_status:
                winner_status.status = 'winner'
                user = User.query.filter_by(user_id=winner_id).first()
                if user:
                    coins = game_session.initial_bank
                    user.balance += coins
                    winner_status.total_coins_earned = coins
                db.session.commit()

            game_session.status = 'finished'
            game_session.finished_at = datetime.utcnow()
            game_session.winner_id = winner_id
            db.session.commit()

            all_player_statuses = PlayerGameStatus.query.filter_by(
                game_session_id=game_session_id_param
            ).all()

            result_data = {
                'winner_id': winner_id,
                'game_session': game_session.to_dict(),
                'player_statistics': [status.to_dict() for status in all_player_statuses],
                'game_finished': True
            }

            print("=== SENDING GAME RESULT TO ALL PLAYERS ===", file=sys.stderr)
            socketio.emit('game_result', result_data)
            socketio.emit('game_finished', {'winner_id': winner_id})

            emit_lobby_update()
            print("Game result events sent successfully", file=sys.stderr)

    except Exception as e:
        print(f"Error in finish_game_with_winner: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def finish_game_without_winner(game_session_id_param):
    try:
        with app.app_context():
            print(f"=== GAME FINISHED WITHOUT WINNER ===", file=sys.stderr)

            game_session = GameSession.query.get(game_session_id_param)
            if not game_session:
                print("Game session not found", file=sys.stderr)
                return

            game_session.status = 'finished'
            game_session.finished_at = datetime.utcnow()
            db.session.commit()

            all_player_statuses = PlayerGameStatus.query.filter_by(
                game_session_id=game_session_id_param
            ).all()
            player_stats = [status.to_dict() for status in all_player_statuses] if all_player_statuses else []
            result_data = {
                'winner_id': None,
                'game_session': game_session.to_dict(),
                'player_statistics': player_stats,
                'game_finished': True,
                'no_winner': True
            }
            print("=== SENDING GAME RESULT (NO WINNER) TO ALL PLAYERS ===", file=sys.stderr)
            socketio.emit('game_result', result_data)
            socketio.emit('game_finished', {'winner_id': None, 'no_winner': True})

            emit_lobby_update()
            print("Game result events sent successfully", file=sys.stderr)

    except Exception as e:
        print(f"Error in finish_game_without_winner: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

@app.route('/api/game/choice', methods=['POST'])
def make_player_choice():
    try:
        data = request.json
        user_id = data.get('user_id')
        game_session_id = data.get('game_session_id')
        round_number = data.get('round_number')
        choice = data.get('choice')

        if not all([user_id, game_session_id, round_number, choice]):
            return jsonify({'error': 'Missing required parameters'}), 400

        if choice not in ['stay', 'leave']:
            return jsonify({'error': 'Invalid choice. Must be "stay" or "leave"'}), 400

        with app.app_context():
            player_status = PlayerGameStatus.query.filter_by(
                game_session_id=game_session_id,
                user_id=user_id,
                status='active'
            ).first()

            if not player_status:
                return jsonify({'error': 'Player not found or not active in game'}), 404

            existing_choice = PlayerChoice.query.filter_by(
                game_session_id=game_session_id,
                round_number=round_number,
                user_id=user_id
            ).first()

            if existing_choice:
                return jsonify({'error': 'Choice already made for this round'}), 400

            player_choice = PlayerChoice(
                game_session_id=game_session_id,
                round_number=round_number,
                user_id=user_id,
                choice=choice
            )

            db.session.add(player_choice)
            db.session.commit()

            print(f"Player {user_id} chose {choice} in round {round_number}", file=sys.stderr)

            return jsonify({
                'message': 'Choice recorded successfully',
                'choice': choice
            }), 200

    except Exception as e:
        print(f"Error in make_player_choice: {str(e)}", file=sys.stderr)
        return jsonify({'error': f'Error recording choice: {str(e)}'}), 500

def finish_game_with_split_bank(game_session_id_param, winners):
    try:
        with app.app_context():
            print(f"=== GAME FINISHED WITH SPLIT BANK ===", file=sys.stderr)
            game_session = GameSession.query.get(game_session_id_param)
            if not game_session:
                print("Game session not found", file=sys.stderr)
                return
            print(f"[LOG] initial_bank в момент дележа: {game_session.initial_bank}", file=sys.stderr)
            bank = game_session.initial_bank or 0
            print(f"[LOG] bank для дележа: {bank}", file=sys.stderr)
            print(f"[LOG] winners: {[w.user_id for w in winners]}", file=sys.stderr)
            if len(winners) == 0 or bank == 0:
                print("No winners or bank is zero for split bank", file=sys.stderr)
                return
            coins_per_winner = bank // len(winners)
            remainder = bank % len(winners)
            winner_statuses = list(winners)
            random.shuffle(winner_statuses)
            all_statuses = PlayerGameStatus.query.filter_by(game_session_id=game_session_id_param).all()
            for status in all_statuses:
                status.total_coins_earned = 0
            for i, player_status in enumerate(winner_statuses):
                user = User.query.filter_by(user_id=player_status.user_id).first()
                if user:
                    extra = 1 if i < remainder else 0
                    coins = coins_per_winner + extra
                    print(f"[LOG] {player_status.user_id} получает {coins} монет (base {coins_per_winner} + extra {extra})", file=sys.stderr)
                    user.balance += coins
                    player_status.status = 'winner'
                    player_status.total_coins_earned = coins
            db.session.commit()
            game_session.status = 'finished'
            game_session.finished_at = datetime.utcnow()
            db.session.commit()
            all_player_statuses = PlayerGameStatus.query.filter_by(
                game_session_id=game_session_id_param
            ).all()
            print("=== PLAYER STATISTICS FOR GAME RESULT ===", file=sys.stderr)
            for s in all_player_statuses:
                print(f"user_id={s.user_id} status={s.status} total_coins_earned={s.total_coins_earned}", file=sys.stderr)
            result_data = {
                'winner_id': None,
                'split_winners': [p.user_id for p in winners],
                'coins_per_winner': coins_per_winner,
                'bank_remainder': remainder,
                'game_session': game_session.to_dict(),
                'player_statistics': [status.to_dict() for status in all_player_statuses],
                'game_finished': True,
                'split_bank': True
            }
            print("=== SENDING SPLIT BANK GAME RESULT TO ALL PLAYERS ===", file=sys.stderr)
            socketio.emit('game_result', result_data)
            socketio.emit('game_finished', {'winner_id': None, 'split_bank': True})
            emit_lobby_update()
            print("Game result events sent successfully", file=sys.stderr)
    except Exception as e:
        print(f"Error in finish_game_with_split_bank: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def lobby_timer_thread():
    global lobby_timer, lobby_timer_running
    print("Lobby timer thread started", file=sys.stderr)
    while True:
        try:
            eventlet.sleep(1)
            with lobby_timer_lock:
                if lobby_timer_running and lobby_timer > 0:
                    lobby_timer -= 1
                    socketio.emit('timer_update', {'time': lobby_timer})
                    print(f"Lobby timer: {lobby_timer} seconds left", file=sys.stderr)
                if lobby_timer == 0:
                    lobby_timer_running = False
                    print("Lobby timer finished", file=sys.stderr)
        except Exception as e:
            print(f"Error in lobby_timer_thread: {e}", file=sys.stderr)
            eventlet.sleep(1)

def start_lobby_timer():
    global lobby_timer, lobby_timer_running
    print("start_lobby_timer called")
    try:
        with lobby_timer_lock:
            lobby_timer = 10
            lobby_timer_running = True
            print(f"Timer set to {lobby_timer} seconds")
        socketio.emit('timer_update', {'time': lobby_timer})
        print("Timer update emitted")
    except Exception as e:
        print(f"Error in start_lobby_timer: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise

@app.route('/api/admin/lobby/<lobby_id>/start_timer', methods=['POST'])
def admin_start_lobby_timer(lobby_id):
    try:
        with app.app_context():
            active_players = Lobby.query.filter_by(
                lobby_id=lobby_id,
                is_active=True
            ).all()

        if not active_players:
            return jsonify({'error': 'No active players in lobby'}), 400

        start_lobby_timer()

        return jsonify({
            'message': 'Timer started successfully',
            'time': lobby_timer
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error starting timer: {str(e)}'
        }), 500

@app.route('/api/admin/lobby/test/start_timer', methods=['POST'])
def test_start_lobby_timer():
    try:
        start_lobby_timer()

        return jsonify({
            'message': 'Test timer started successfully',
            'time': lobby_timer
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error starting test timer: {str(e)}'
        }), 500

def start_lobby_timer_thread():
    try:
        eventlet.spawn(lobby_timer_thread)
        print("Lobby timer thread started successfully", file=sys.stderr)
    except Exception as e:
        print(f"Error starting lobby timer thread: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)

start_lobby_timer_thread()

@app.route('/api/game/status', methods=['GET'])
def get_game_status():
    lobby_id = request.args.get('lobby_id')
    if not lobby_id:
        return jsonify({'error': 'Missing lobby_id'}), 400

    game_session = GameSession.query.filter_by(lobby_id=lobby_id).first()
    if not game_session:
        return jsonify({'status': 'waiting'}), 200

    return jsonify(game_session.to_dict()), 200

@app.route('/api/game/player-status', methods=['GET'])
def get_player_status():
    user_id = request.args.get('user_id')
    lobby_id = request.args.get('lobby_id')

    if not user_id or not lobby_id:
        return jsonify({'error': 'Missing user_id or lobby_id'}), 400

    game_session = GameSession.query.filter_by(lobby_id=lobby_id).first()
    if not game_session:
        return jsonify({'status': 'not_in_game'}), 200

    player_status = PlayerGameStatus.query.filter_by(
        game_session_id=game_session.id,
        user_id=user_id
    ).first()

    if not player_status:
        return jsonify({'status': 'not_found'}), 200

    return jsonify({
        'status': player_status.status,
        'eliminated_in_round': player_status.eliminated_in_round,
        'quit_in_round': player_status.quit_in_round,
        'total_coins_earned': player_status.total_coins_earned
    }), 200

@app.route('/api/game/round/start', methods=['POST'])
def start_round():
    data = request.json
    game_session_id = data.get('game_session_id')
    round_number = data.get('round_number', 1)

    if not game_session_id:
        return jsonify({'error': 'Missing game_session_id'}), 400

    game_round = GameRound(
        game_session_id=game_session_id,
        round_number=round_number
    )
    db.session.add(game_round)
    db.session.commit()

    return jsonify({
        'message': 'Round started successfully',
        'round': game_round.to_dict()
    }), 200

@app.route('/api/game/round/end', methods=['POST'])
def end_round():
    data = request.json
    game_session_id = data.get('game_session_id')
    round_number = data.get('round_number')
    eliminated_players = data.get('eliminated_players', [])

    if not game_session_id or not round_number:
        return jsonify({'error': 'Missing required parameters'}), 400

    game_round = GameRound.query.filter_by(
        game_session_id=game_session_id,
        round_number=round_number
    ).first()

    if game_round:
        game_round.ended_at = datetime.utcnow()
        game_round.eliminated_players = json.dumps(eliminated_players)
        db.session.commit()

    game_session = GameSession.query.get(game_session_id)
    if game_session:
        game_session.current_round = round_number + 1
        db.session.commit()

    return jsonify({
        'message': 'Round ended successfully',
        'eliminated_players': eliminated_players
    }), 200

@app.route('/api/game/finish', methods=['POST'])
def finish_game():
    data = request.json
    winner_id = data.get('winner_id')

    if not winner_id:
        return jsonify({'error': 'Missing winner_id'}), 400

    try:
        socketio.emit('game_finished', {
            'winner_id': winner_id,
            'message': 'Game finished!'
        })

        return jsonify({
            'message': 'Game finished successfully',
            'winner_id': winner_id
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error finishing game: {str(e)}'
        }), 500

@app.route('/api/admin/lobbies', methods=['GET'])
def get_all_lobbies():
    try:
        lobbies = db.session.query(Lobby.lobby_id).distinct().all()
        lobby_list = []

        for (lobby_id,) in lobbies:
            active_players = Lobby.query.filter_by(
                lobby_id=lobby_id,
                is_active=True
            ).filter(Lobby.user_id != 'Loujder').count()

            game_session = GameSession.query.filter_by(lobby_id=lobby_id).first()
            status = game_session.status if game_session else 'waiting'

            lobby_list.append({
                'lobby_id': lobby_id,
                'player_count': active_players,
                'status': status
            })

        return jsonify({
            'lobbies': lobby_list,
            'total_count': len(lobby_list)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error getting lobbies: {str(e)}'
        }), 500

@app.route('/api/admin/lobby/<lobby_id>/start', methods=['POST'])
def admin_start_game(lobby_id):
    try:
        print(f"=== ADMIN START GAME DEBUG ===", file=sys.stderr)
        print(f"Starting game for lobby: {lobby_id}", file=sys.stderr)
        all_lobby_players = Lobby.query.filter_by(lobby_id=lobby_id, is_active=True, is_admin=False, is_observer=False).all()
        print("[LOG] Все игроки в лобби перед стартом:", file=sys.stderr)
        for p in all_lobby_players:
            print(f"[LOG] user_id={p.user_id} nickname={p.nickname} is_ready={p.is_ready}", file=sys.stderr)
        ready_players = [p for p in all_lobby_players if p.is_ready]
        print(f"[LOG] Игроки с is_ready=True при старте игры: {[f'{p.user_id} ({p.nickname})' for p in ready_players]}", file=sys.stderr)
        if not ready_players:
            print("[LOG] Нет готовых игроков для старта игры", file=sys.stderr)
            return jsonify({'error': 'No ready players in lobby'}), 400
        initial_bank = len(ready_players)
        print(f"[LOG] initial_bank при старте игры: {initial_bank}", file=sys.stderr)
        non_admin_players = [p for p in ready_players if p.user_id != 'Loujder']
        total_rounds = calculate_total_rounds(len(non_admin_players))
        print(f"Calculated {total_rounds} total rounds for {len(non_admin_players)} non-admin players", file=sys.stderr)
        existing_session = GameSession.query.filter_by(lobby_id=lobby_id).first()
        if existing_session:
            print(f"Found existing session {existing_session.id} with status: {existing_session.status}", file=sys.stderr)
            if existing_session.status != 'finished':
                print(f"Finishing existing session {existing_session.id}", file=sys.stderr)
                existing_session.status = 'finished'
                existing_session.finished_at = datetime.utcnow()
                db.session.commit()
                print("Existing session finished", file=sys.stderr)
            else:
                print("Existing session is already finished", file=sys.stderr)
        GameSession.query.filter_by(lobby_id=lobby_id).delete()
        db.session.commit()
        print("Cleaned up existing game sessions", file=sys.stderr)
        print("Creating game session...", file=sys.stderr)
        try:
            game_session = GameSession(
                lobby_id=lobby_id,
                status='playing',
                total_rounds=total_rounds,
                initial_bank=initial_bank
            )
            db.session.add(game_session)
            db.session.commit()
            print(f"Game session created successfully with ID: {game_session.id}, total_rounds: {total_rounds}", file=sys.stderr)
        except Exception as e:
            print(f"Error creating game session: {str(e)}", file=sys.stderr)
            print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
            raise
        print("Starting game timer...", file=sys.stderr)
        try:
            initialize_player_statuses(game_session.id, lobby_id)
            start_game_timer(game_session.id)
            print("Game timer started successfully", file=sys.stderr)
        except Exception as e:
            print(f"Error starting game timer: {str(e)}", file=sys.stderr)
            print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
            raise
        try:
            socketio.emit('game_started', {
                'game_session': game_session.to_dict(),
                'players': [player.to_dict() for player in ready_players]
            })
            print("Game started event sent to all players", file=sys.stderr)
        except Exception as e:
            print(f"Error sending game started event: {str(e)}", file=sys.stderr)
        print("=== ADMIN START GAME SUCCESS ===", file=sys.stderr)
        return jsonify({
            'message': 'Game started successfully by admin',
            'game_session': game_session.to_dict()
        }), 200
    except Exception as e:
        print(f"=== ADMIN START GAME ERROR ===", file=sys.stderr)
        print(f"Error in admin_start_game: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({
            'error': f'Error starting game: {str(e)}'
        }), 500

@app.route('/api/admin/lobby/<lobby_id>/delete', methods=['DELETE'])
def admin_delete_lobby(lobby_id):
    try:
        print(f"=== DELETING LOBBY {lobby_id} ===", file=sys.stderr)

        game_session = GameSession.query.filter_by(lobby_id=lobby_id).first()

        if game_session:
            game_session_id = game_session.id
            print(f"Found game session with ID: {game_session_id}", file=sys.stderr)

            PlayerChoice.query.filter_by(game_session_id=game_session_id).delete()
            print("Deleted player choices", file=sys.stderr)

            PlayerGameStatus.query.filter_by(game_session_id=game_session_id).delete()
            print("Deleted player game statuses", file=sys.stderr)

            GameRound.query.filter_by(game_session_id=game_session_id).delete()
            print("Deleted game rounds", file=sys.stderr)

            GameSession.query.filter_by(lobby_id=lobby_id).delete()
            print("Deleted game session", file=sys.stderr)

        Lobby.query.filter_by(lobby_id=lobby_id).delete()
        print("Deleted lobby entries", file=sys.stderr)

        db.session.commit()
        print(f"=== LOBBY {lobby_id} DELETED SUCCESSFULLY ===", file=sys.stderr)

        return jsonify({
            'message': 'Lobby deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"=== ERROR DELETING LOBBY {lobby_id} ===", file=sys.stderr)
        print(f"Error: {str(e)}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({
            'error': f'Error deleting lobby: {str(e)}'
        }), 500

@app.route('/api/admin/lobby/create', methods=['POST'])
def admin_create_lobby():
    data = request.json
    admin_id = data.get('admin_id')
    lobby_id = data.get('lobby_id')

    if not admin_id or not lobby_id:
        return jsonify({'error': 'Missing admin_id or lobby_id'}), 400
    if admin_id != 'Loujder':
        return jsonify({'error': 'Only admin can create lobby'}), 403

    existing = Lobby.query.filter_by(lobby_id=lobby_id, is_active=True).first()
    if existing:
        return jsonify({'error': 'Lobby already exists'}), 400

    lobby_entry = Lobby(
        lobby_id=lobby_id,
        user_id=admin_id,
        nickname='Admin',
        is_active=True,
        is_admin=True
    )
    db.session.add(lobby_entry)
    db.session.commit()
    return jsonify({'message': 'Lobby created', 'lobby_id': lobby_id}), 201

def calculate_total_rounds(player_count):
    if player_count <= 1:
        return 1

    rounds = 0
    current_players = player_count

    while current_players > 1:
        eliminated = current_players // 2
        current_players = current_players - eliminated
        rounds += 1

    return rounds

def initialize_player_statuses(game_session_id, lobby_id=None):
    try:
        with app.app_context():
            game_session = GameSession.query.get(game_session_id)
            if not game_session:
                print(f"Game session {game_session_id} not found", file=sys.stderr)
                return

            lobby_id = lobby_id or game_session.lobby_id

            active_players = Lobby.query.filter_by(
                lobby_id=lobby_id,
                is_active=True
            ).filter(Lobby.user_id != 'Loujder').all()

            print(f"Found {len(active_players)} active players in lobby {lobby_id}", file=sys.stderr)

            for player in active_players:
                existing_status = PlayerGameStatus.query.filter_by(
                    game_session_id=game_session_id,
                    user_id=player.user_id
                ).first()

                if not existing_status:
                    player_status = PlayerGameStatus(
                        game_session_id=game_session_id,
                        user_id=player.user_id,
                        status='active'
                    )
                    db.session.add(player_status)
                    print(f"Added player status for {player.user_id}", file=sys.stderr)

            db.session.commit()
            print(f"Initialized player statuses for {len(active_players)} players in lobby {lobby_id}", file=sys.stderr)

    except Exception as e:
        print(f"Error initializing player statuses: {str(e)}", file=sys.stderr)
        db.session.rollback()

def get_active_players(game_session_id):
    try:
        with app.app_context():
            active_statuses = PlayerGameStatus.query.filter_by(
                game_session_id=game_session_id,
                status='active'
            ).all()

            return active_statuses

    except Exception as e:
        print(f"Error getting active players: {str(e)}", file=sys.stderr)
        return []

def eliminate_players_in_round(game_session_id, round_number):
    try:
        with app.app_context():
            active_players = get_active_players(game_session_id)

            if len(active_players) <= 1:
                return active_players

            eliminate_count = len(active_players) // 2

            players_to_eliminate = random.sample(active_players, eliminate_count)

            for player_status in players_to_eliminate:
                player_status.status = 'eliminated'
                player_status.eliminated_in_round = round_number

            db.session.commit()

            eliminated_player_ids = [p.user_id for p in players_to_eliminate]
            socketio.emit('players_eliminated', {
                'eliminated_players': eliminated_player_ids,
                'round_number': round_number,
                'remaining_count': len(active_players) - eliminate_count
            })
            print(f"Players eliminated event sent: {eliminated_player_ids}", file=sys.stderr)

            remaining_players = [p for p in active_players if p not in players_to_eliminate]

            print(f"Eliminated {eliminate_count} players in round {round_number}, {len(remaining_players)} remaining", file=sys.stderr)

            return remaining_players

    except Exception as e:
        print(f"Error eliminating players: {str(e)}", file=sys.stderr)
        db.session.rollback()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)