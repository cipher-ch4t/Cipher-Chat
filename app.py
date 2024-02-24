from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_cors import CORS
from datetime import datetime, timezone
from flask_login import LoginManager, login_required, logout_user, UserMixin, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = '7841'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/cipherchat_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    date_of_birth = db.Column(db.String(50), unique=False, nullable=False)
    messages_sent = db.relationship('Message', backref='sender', lazy=True, foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='receiver', lazy=True, foreign_keys='Message.receiver_id')

    def __init__(self, username, password, name, email, date_of_birth):
        self.username = username
        self.password = generate_password_hash(password)
        self.name = name
        self.email = email
        self.date_of_birth = date_of_birth

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Message {self.id}>'

    def messages_with(self, other_user):
        return Message.query.filter(
            (Message.sender == self and Message.receiver == other_user) |
            (Message.sender == other_user and Message.receiver == self)
        ).order_by(Message.timestamp)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@app.route('/search', methods=['GET'])
@login_required
def search_users():
    try:
        search_value = request.args.get('searchValue')
        # Query the database to find users
        users = User.query.filter(User.username.like(f"%{search_value}%")).all()
        # Return usernames and user IDs as JSON
        user_data = [{'username': user.username, 'id': user.id} for user in users]
        return jsonify(user_data)
    except Exception as e:
        return str(e)


@login_required
@app.route('/chat/<username>')
def chat(username):
    other_user = User.query.filter_by(username=username).first()

    if current_user:
        # Get messages for the current user (replace this with your logic)
        messages = current_user.messages_with(other_user)
        return render_template('chat.html', username=username, messages=messages)
    else:
        flash('User not found', 'error')
        return redirect(url_for('login'))


@socketio.on('send_message')
def handle_message(data):
    sender = User.query.filter_by(username=data['sender']).first()
    content = data['content']

    if sender:
        message = Message(sender_id=sender.id, content=content)
        db.session.add(message)
        db.session.commit()

        # Broadcast the message to all connected clients
        emit('receive_message', {'sender': sender.username, 'content': content}, broadcast=True)
    else:
        emit('error', {'message': 'User not found'})


@app.route('/search_page')
@login_required
def search_page():
    return render_template('search.html')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Handle form submissions
        new_password = request.form.get('new_password')
        new_username = request.form.get('new_username')
        # Add similar lines for other form fields like profile picture, email, etc.

        # Update user information in the database
        if new_password:
            current_user.password = new_password
        if new_username:
            current_user.username = new_username
        # Add similar lines for other user information updates

        db.session.commit()

        # Optionally, you can flash a message to indicate success
        flash('Settings updated successfully!', 'success')

        # Redirect to the updated settings or profile page
        return redirect(url_for('settings'))

    # Render the settings page with the current user's information
    return render_template('profile.html', user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        name = request.form['name']
        date_of_birth = request.form['date_of_birth']
        email = request.form['email']
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Use the actual user-entered password in generate_password_hash
        new_user = User(username=username, password=generate_password_hash(password), name=name, email=email,
                        date_of_birth=date_of_birth)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Authentication successful, redirect to chat page
            flash('Login successful!', 'success')
            return redirect(url_for('chat', username=username))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


def update_password(user, new_password):
    # Update user's password in the database
    user.set_password(new_password)
    db.session.commit()


@app.route('/logout', methods=['POST'])
def logout():
    # Use flask_login's logout_user() to log the user out
    logout_user()

    # Redirect to the login page after logout
    return redirect(url_for('login'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    app.logger.info('Reached the forgot_password route')  # Add this line
    if request.method == 'POST':
        username = request.form.get('username')
        date_of_birth = request.form.get('date_of_birth')

        user = User.query.filter_by(username=username,
                                    date_of_birth=datetime.strptime(date_of_birth, '%m-%d-%Y')).first()

        if user:
            flash(f'We have sent a password reset token to your registered email address.', 'info')
        else:
            flash('Invalid username or date of birth. Please try again.', 'danger')

        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/public_profile/<int:user_id>')
@login_required
def public_profile(user_id):
    # Fetch user information based on user_id from the database
    user = User.query.get(user_id)

    return render_template('public_profile.html', user=user)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
