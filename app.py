from flask import Flask, request, render_template, redirect, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, abort, fields, marshal_with
from tokenize import String
from sqlalchemy import desc

import requests

import json
from PIL import Image
from datetime import datetime
import os

import string

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///D:\mad project\Bloglite\database.db'
db = SQLAlchemy(app)


class User(db.Model):

    __tablename__ = 'users'

    username = db.Column(db.String(80), nullable=False, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    profile_picture = db.Column(db.String(120))

    def __init__(self, username, email, password, first_name, last_name, profile_picture):
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name    
        self.profile_picture = profile_picture

class Followers(db.Model):

    __tablename__ = 'followers'

    username = db.Column(db.String(80), primary_key=True)
    following = db.Column(db.String(120), primary_key=True)

    def __init__(self, username, following):
        self.username = username
        self.following = following

class articles(db.Model):
    __tablename__ = 'articles'
    post_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(120))
    timestamp = db.Column(db.String, nullable=False)

    def __init__(self, username, title, content, image, timestamp):
        self.username = username
        self.title = title
        self.content = content
        self.image = image
        self.timestamp = timestamp

class post_stats(db.Model):
    __tablename__ = 'post_stats'
    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), primary_key=True)
    like = db.Column(db.Integer)
    comment = db.Column(db.String(120))

    def __init__(self, post_id, user_id, like, comment):
        self.post_id = post_id
        self.user_id = user_id
        self.like = like
        self.comment = comment

#parsers for api
#user update parser
user_update_parser = reqparse.RequestParser()
user_update_parser.add_argument('username', type=str)
user_update_parser.add_argument('email', type=str)
user_update_parser.add_argument('password', type=str)
user_update_parser.add_argument('first_name', type=str)
user_update_parser.add_argument('last_name', type=str)
user_update_parser.add_argument('profile_picture', type=str)

#user create parser
user_create_parser = reqparse.RequestParser()
user_create_parser.add_argument('username', type=str)
user_create_parser.add_argument('email', type=str)
user_create_parser.add_argument('password', type=str)
user_create_parser.add_argument('first_name', type=str)
user_create_parser.add_argument('last_name', type=str)
user_create_parser.add_argument('profile_picture', type=str)

#post create/update parser
post_create_parser = reqparse.RequestParser()
post_create_parser.add_argument('username', type=str)
post_create_parser.add_argument('title', type=str)
post_create_parser.add_argument('content', type=str)
post_create_parser.add_argument('image', type=str)
post_create_parser.add_argument('timestamp', type=str)


#api resources
user_fields = {
    'username': fields.String,
    'email': fields.String,
    'password': fields.String,
    'first_name': fields.String,
    'last_name': fields.String,
    'profile_picture': fields.String
}

post_fields = {
    'post_id': fields.Integer,
    'username': fields.String,
    'title': fields.String,
    'content': fields.String,
    'image': fields.String,
    'timestamp': fields.String
}


#APIs
class userAPI(Resource):
    
    #fetch profile
    @marshal_with(user_fields)
    def get(self, username):
        user = User.query.filter_by(username=username).first()
        
        if user:
            return user, 200
        else:
            #return 404 if user not found
            
            return abort(404, message="User not found")
             

    #update profile
    @marshal_with(user_fields)
    def put(self, username):

        args = user_update_parser.parse_args()
        user = User.query.filter_by(username=username).first()
        user.email = args.get('email', user.email)
        user.password = args.get('password', user.password)
        user.first_name = args.get('first_name', user.first_name)
        user.last_name = args.get('last_name', user.last_name)
        user.profile_picture = args.get('profile_picture', user.profile_picture)
        db.session.add(user)
        db.session.commit()
        return user, 200
        

    #delete profile

    def delete(self, username):
        user = User.query.filter_by(username=username).first()
        if user:
            all_articles = articles.query.filter_by(username=username)
            for article in all_articles:
                db.session.delete(article)
            all_followers = Followers.query.filter_by(username=username)
            for follower in all_followers:
                db.session.delete(follower)
            all_following = Followers.query.filter_by(following=username)
            for following in all_following:
                db.session.delete(following)
            all_post_stats = post_stats.query.filter_by(user_id=username)
            for post_stat in all_post_stats:
                db.session.delete(post_stat)
            db.session.delete(user)
            db.session.commit()
            return 'User deleted'
        else:
            abort(404, message="User not found")

    #create profile
    @marshal_with(user_fields)
    def post(self):
        
        args = user_create_parser.parse_args()
        uname = args.get('username', None)
        uemail = args.get('email', None)
        upass = args.get('password', None)
        ufname = args.get('first_name', None)
        ulname = args.get('last_name', None)
        upf = args.get('profile_picture', None)
        user = User(username=uname, email=uemail, password=upass, first_name=ufname, last_name=ulname, profile_picture=upf)
        db.session.add(user)
        db.session.commit()
        return user, 201

class postAPI(Resource):

    #get request for posts
    @marshal_with(post_fields)
    def get(self, post_id):
        
        posts = articles.query.filter_by(post_id=post_id).first()
        if posts:
            return posts, 200
        else:
            abort(404, message="posts not found")

    @marshal_with(post_fields)
    def post(self):
        args = post_create_parser.parse_args()
        uname = args.get('username', None)
        utitle = args.get('title', None)
        ucontent = args.get('content', None)
        uimage = args.get('image', None)
        utimestamp = args.get('timestamp', None)
        print(uname, utitle, ucontent, uimage, utimestamp)
        post = articles(username=uname, title=utitle, content=ucontent, image=uimage, timestamp=utimestamp)
        db.session.add(post)
        db.session.commit()
        return post, 201

    #update post
    @marshal_with(post_fields)
    def put(self, post_id):
        args = post_create_parser.parse_args()
        post = articles.query.filter_by(post_id=post_id).first()
        post.username = args.get('username', post.username)
        post.title = args.get('title', post.title)
        post.content = args.get('content', post.content)
        post.image = args.get('image', post.image)
        post.timestamp = args.get('timestamp', post.timestamp)
        db.session.add(post)
        db.session.commit()
        return post, 200

    #delete post
    def delete(self, post_id):
        post_id = int(post_id)
        post = articles.query.filter_by(post_id=post_id).first()
        if post:
            db.session.delete(post)
            db.session.commit()
            return 'post deleted'
        else:
            abort(404, message="post not found")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        USERNAME = request.form['username']
        PASSWORD = request.form['password']
        user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(USERNAME))
        if user.status_code == 200:
            if user.json()['password'] == PASSWORD:
                return redirect('/{}/dashboard'.format(USERNAME))
            else:
                return render_template('login.html', error='Invalid username or password')
        else:
            return render_template('login.html', error='Invalid username or password')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        pf = request.files['profile_picture']

        if len(password) == 6:
            for i in range(len(password)):
                if i<3:
                    if password[i] in string.ascii_letters:
                        continue
                    else:
                        return render_template('signup.html', error="Password not satisfied the requirnments")
                elif i>=3 and i<5:
                    if password[i] in string.digits:
                        continue
                    else:
                        return render_template('signup.html', error="Password not satisfied the requirnments")
                elif i==5:
                    if password[i] in string.punctuation:
                        continue
                else:
                    return render_template('signup.html', error="Password not satisfied the requirnments")
        else:
            return render_template('signup.html', error="Password not satisfied the requirnments")

        #get request on api
        user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
        if user.status_code == 200:
            return render_template('signup.html', error='Username or email already exists')
        else:
            #post request on api
            if pf:
                d = {
                    'username': username, 
                    'email': email, 
                    'password': password, 
                    'first_name': first_name, 
                    'last_name': last_name, 
                    'profile_picture': '{}.png'.format(username)
                    }
                user = requests.post('http://127.0.0.1:5000/api/user', json=d)
                img = Image.open(pf)
                img.save('D:\mad project\Bloglite\static\profile_pictures\{}.png'.format(username))
                return redirect('/')
            else:
                d = {
                    'username': username, 
                    'email': email, 
                    'password': password, 
                    'first_name': first_name, 
                    'last_name': last_name, 
                    'profile_picture': 'default.png'
                    }
                user = requests.post('http://127.0.0.1:5000/api/user', json=d)
                return redirect('/')

@app.route('/<string:username>')
def profile(username):
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    if user.status_code == 200:
        return render_template('profile.html', user=user.json())
    else:
        return render_template('error.html')

@app.route('/<string:username>/edit_profile', methods=['GET', 'POST'])
def edit_profile(username):
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    if request.method == 'GET':
        if user.status_code == 200:
            return render_template('edit_profile.html', user=user.json())
        else:
            return render_template('error.html')

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        pf = request.files['profile_picture']
        PASSWORD = user.json()['password']
        #put request on api

        if password == PASSWORD:
            if not pf:
                pf = user.json()['profile_picture']
                d = {
                        'email': email, 
                        'password': password, 
                        'first_name': first_name, 
                        'last_name': last_name, 
                        'profile_picture': pf
                    }
                user = requests.put('http://127.0.0.1:5000/api/user/{}'.format(username), json=d)
                return redirect('/{}'.format(username))
            else:
                d = {
                        'email': email, 
                        'password': password, 
                        'first_name': first_name, 
                        'last_name': last_name, 
                        'profile_picture': '{}.png'.format(username)
                    }
                if user.json()['profile_picture'] != 'default.png':
                    os.remove('D:\mad project\Bloglite\static\profile_pictures\{}'.format(user.json()['profile_picture']))
                user = requests.put('http://127.0.0.1:5000/api/user/{}'.format(username), json=d)
                
                img = Image.open(pf)
                img.save('D:\mad project\Bloglite\static\profile_pictures\{}.png'.format(username))
                return redirect('/{}'.format(username))

        else:
            return render_template('edit_profile.html', error='Invalid password', user=user.json())
            
        
@app.route('/<string:username>/dashboard', methods=['GET', 'POST'])
def dashboard(username):
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    following = Followers.query.filter_by(username=username).all()
    posts = []
    if following:
        for i in following:
            posts+=(articles.query.filter_by(username=i.following).all())
        
        posts.sort(key=lambda x: x.timestamp, reverse=True)
    
    session = db.scoped_session(db.sessionmaker())
    ids = session.query(post_stats).join(articles, articles.post_id == post_stats.post_id, isouter=True)
    result = db.session.execute(str(ids)).fetchall()
    session.close()
    likes = []
    for i in result:
        if i[2] == True:
            likes.append(i[0])
    if request.method == 'GET':
        resp =  make_response(render_template('dashboard.html', user=user.json(), posts = posts, liked_posts=likes))
        resp.set_cookie('url', request.url)
        return resp

@app.route('/<string:username>/delete', methods=['GET', 'POST'])
def delete(username):
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    if request.method == 'GET':
        if user.status_code == 200:
            requests.delete('http://127.0.0.1:5000/api/user/{}'.format(username))
            return redirect('/')
        else:
            return render_template('error.html')

@app.route('/<string:username>/create_post', methods=['GET', 'POST'])
def create_post(username):
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    if request.method == 'GET':
        return render_template('create_post.html', user=user.json())
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        pp = request.files['image']
        timestamp = datetime.now()
        
        if pp:
            posts = articles.query.filter_by(username=username).all()
           
            if posts:
                post_id = posts[-1].post_id+ 1
            else:
                post_id = 1
            d = {
                'username': username,
                'title': title,
                'content': content,
                'image': '{}.png'.format(post_id),
                'timestamp': (timestamp.strftime('%Y/%m/%d %H:%M:%S'))
            }
            
            post = requests.post('http://127.0.0.1:5000/api/post', json=d)
            img = Image.open(pp)
            img.save('D:\mad project\Bloglite\static\post_images\{}.png'.format(post_id))
            return redirect('/{}/dashboard'.format(username))

        else:
            d = {
                'username': username,
                'title': title,
                'content': content,
                'image': None, 
                'timestamp': (timestamp.strftime('%Y/%m/%d %H:%M:%S'))
            }
            post = requests.post('http://127.0.0.1:5000/api/post', json=d)
            return redirect('/{}/dashboard'.format(username))

@app.route('/<string:username>/posts')
def posts(username):
    user = requests.get('http://127.0.0.1:5000/api/user/{username}'.format(username=username))
    posts = articles.query.filter_by(username=username).all()
    if posts:
        return render_template('posts.html', posts=posts, user=user.json())
    else:
        return render_template('posts.html', user=user.json(), mssg='No posts yet')

@app.route('/<string:username>/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(username, post_id):
    post = requests.get('http://127.0.0.1:5000/api/post/{}'.format(post_id))
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    
    if request.method == 'GET':
        return render_template('edit_post.html', post=post.json(), user=user.json())

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        pp = request.files['image']
        if pp:
            d = {
                'username': username,
                'title': title,
                'content': content,
                'image': '{}.png'.format(post_id),
                'timestamp': post.json()['timestamp']
            }
            if post.json()['image'] != None:
                os.remove('D:\mad project\Bloglite\static\{}'.format(post.json()['image']))
            post = requests.put('http://127.0.0.1:5000/api/post/{}'.format(post_id), json=d)
            img = Image.open(pp)
            img.save('D:\mad project\Bloglite\static\{}.png'.format(post_id))
            return redirect('/{}/posts'.format(username))

        else:
            d = {
                'username': username,
                'title': title,
                'content': content,
                'image': post.json()['image'],
                'timestamp': post.json()['timestamp']
            }
            post = requests.put('http://127.0.0.1:5000/api/post/{}'.format(post_id), json=d)
            return redirect('/{}/posts'.format(username))
    
@app.route('/<string:username>/delete_post/<int:post_id>', methods=['GET'])
def delete_post(username, post_id):
    if request.method == 'GET':
        post = requests.get('http://127.0.0.1:5000/api/post/{}'.format(post_id))
        like_post = post_stats.query.filter_by(post_id=post_id).all()
        for i in like_post:
            db.session.delete(i)
            db.session.commit()
        if post.json()['image'] != None:
            os.remove('D:\mad project\Bloglite\static\post_images\{}'.format(post.json()['image']))
        post = requests.delete('http://127.0.0.1:5000/api/post/{}'.format(post_id))
        return redirect('/{}/posts'.format(username))

@app.route('/<string:username>/search', methods=['GET', 'POST'])
def search(username):
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    following = Followers.query.filter_by(username=username).all()
    for i in range(len(following)):
        following[i] = following[i].following
    if request.method == 'POST':
        search = request.form['search']
        profiles = User.query.filter(User.first_name.like('%{}%'.format(search))).all()
        profiles += User.query.filter(User.last_name.like('%{}%'.format(search))).all()
        profiles += User.query.filter(User.username.like('%{}%'.format(search))).all()
        profiles = list(set(profiles))
        if profiles:
            resp =  make_response(render_template('search.html', profiles=profiles, user=user.json(), following=following))
            resp.set_cookie('search', search)
            resp.set_cookie('url', '/{}/search'.format(username))
            return resp
        else:
            
            return (render_template('search.html', mssg='No results found', user=user.json(), following=following))
            

    if request.method == 'GET':
        search = request.cookies.get('search')
        print(search)
        profiles = User.query.filter(User.first_name.like('%{}%'.format(search))).all()
        profiles += User.query.filter(User.last_name.like('%{}%'.format(search))).all()
        profiles += User.query.filter(User.username.like('%{}%'.format(search))).all()
        profiles = list(set(profiles))
        return render_template('search.html', user=user.json(), following=following, profiles=profiles)

@app.route('/<string:username>/profile/<string:profile_username>', methods=['GET'])
def user_profile(username, profile_username):
    user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
    profile = requests.get('http://127.0.0.1:5000/api/user/{}'.format(profile_username))
    posts = articles.query.filter_by(username=profile_username).all()
    posts.reverse()
    following = Followers.query.filter_by(username=username).all()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
    for i in range(len(following)):
        following[i] = following[i].following
    
    session = db.scoped_session(db.sessionmaker())
    ids = session.query(post_stats).join(articles, articles.post_id == post_stats.post_id, isouter=True)
    result = db.session.execute(str(ids)).fetchall()
    session.close()
    likes = []
    for i in result:
        if i[2] == True:
            likes.append(i[0])
    
    resp =  make_response(render_template('user_profile.html', user=user.json(), posts=posts, following= following, profile=profile.json(), liked_posts=likes))
    resp.set_cookie('url', '/{}/profile/{}'.format(username, profile_username))
    return resp

@app.route('/<string:username>/post/like/<int:post_id>', methods=['GET'])
def like_post(username, post_id):
    if request.method == 'GET':
        like = post_stats(user_id=username, post_id=post_id, like=True, comment=None)
        db.session.add(like)
        db.session.commit()
        return redirect(request.cookies.get('url'))

@app.route('/<string:username>/post/unlike/<int:post_id>', methods=['GET'])
def unlike_post(username, post_id):
    if request.method == 'GET':
        like = post_stats.query.filter_by(user_id=username, post_id=post_id).first()
        if like.comment == None:
            db.session.delete(like)
            db.session.commit()
        else:
            like.like = False
            db.session.commit()
        return redirect(request.cookies.get('url'))

@app.route('/<string:username>/post/comment/<int:post_id>', methods=['GET', 'POST'])
def comment_post(username, post_id):
    if request.method == 'POST':
        comment = request.form['comment']
        like = post_stats.query.filter_by(user_id=username, post_id=post_id).first()
        if like:
            like.comment = comment
            db.session.commit()
        else:
            comment = post_stats(user_id=username, post_id=post_id,like=False, comment=comment)
            db.session.add(comment)
            db.session.commit()
        return redirect(request.cookies.get('url'))

@app.route('/<string:username>/follow/<string:user_username>', methods=['GET'])
def follow(username, user_username):
    if request.method == 'GET':
        following = Followers(username=username, following=user_username)
        db.session.add(following)
        db.session.commit()
        return redirect(request.cookies.get('url'))

@app.route('/<string:username>/unfollow/<string:user_username>', methods=['GET'])
def unfollow(username, user_username):
    if request.method == 'GET':
        following = Followers.query.filter_by(username=username, following=user_username).first()
        db.session.delete(following)
        db.session.commit()
        return redirect(request.cookies.get('url'))

@app.route('/<string:username>/following', methods=['GET'])
def following(username):
    if request.method == 'GET':
        user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
        following = Followers.query.filter_by(username=username).all()
        for i in range(len(following)):
            following[i] = User.query.filter_by(username=following[i].following).first()
        return render_template('following.html', following=following, user=user.json())

@app.route('/<string:username>/followers', methods=['GET'])
def followers(username):
    if request.method == 'GET':
        user = requests.get('http://127.0.0.1:5000/api/user/{}'.format(username))
        followers = Followers.query.filter_by(following=username).all()
        for i in range(len(followers)):
            followers[i] = User.query.filter_by(username=followers[i].username).first()
        return render_template('followers.html', followers=followers, user=user.json())


api.add_resource(userAPI, '/api/user/<string:username>', '/api/user')
api.add_resource(postAPI, '/api/post/<int:post_id>', '/api/post')

if __name__ == '__main__':
    app.run(debug=True)