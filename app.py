from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import markdown2


app = Flask(__name__)

# Use environment variable for secret key
app.config['SECRET_KEY'] = 'skyligitsfsfssd'

# Use environment variable for the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure session to be more secure
app.config['SESSION_COOKIE_SECURE'] = True

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    author = db.Column(db.String(20))
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.Text)

@app.route('/')
def index():
    posts = Blogpost.query.order_by(Blogpost.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Blogpost.query.get(post_id)
    if post:
        return render_template('post.html', post=post)
    else:
        return render_template('error.html', error='Post not found')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            return redirect(url_for('addpost'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# ... (previous code)

@app.route('/addpost', methods=['GET', 'POST'])
def addpost():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            title = request.form['title']
            subtitle = request.form['subtitle']
            author = request.form['author']
            content = request.form['content']

            # Convert Markdown to HTML
            content_html = markdown2.markdown(content)

            post = Blogpost(title=title, subtitle=subtitle, author=author, content=content_html, date_posted=datetime.utcnow())

            with app.app_context():
                db.session.add(post)
                db.session.commit()

            return redirect(url_for('index'))
        else:
            return render_template('add.html')
    else:
        return redirect(url_for('login'))

@app.route('/editpost/<int:post_id>', methods=['GET', 'POST'])
def editpost(post_id):
    post = Blogpost.query.get(post_id)

    if not post:
        return render_template('error.html', error='Post not found')

    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            # Update post details based on form submission
            post.title = request.form['title']
            post.subtitle = request.form['subtitle']
            post.author = request.form['author']
            content = request.form['content']

            # Convert Markdown to HTML
            content_html = markdown2.markdown(content)

            post.content = content_html
            post.date_posted = datetime.utcnow()

            db.session.commit()
            return redirect(url_for('index'))

        return render_template('edit.html', post=post)
    else:
        return redirect(url_for('login'))


@app.route('/delete/<int:post_id>')
def delete(post_id):
    post = Blogpost.query.get(post_id)

    if not post:
        return render_template('error.html', error='Post not found')

    if 'logged_in' in session and session['logged_in']:
        db.session.delete(post)
        db.session.commit()

        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Check if the admin user already exists
        admin_user = User.query.filter_by(username='admin').first()

        if not admin_user:
            # Create the admin user and add it to the database
            admin_password = generate_password_hash('password', method='sha256')
            admin_user = User(username='admin', password=admin_password)
            with app.app_context():
                db.session.add(admin_user)
                db.session.commit()

    app.run(debug=True)
