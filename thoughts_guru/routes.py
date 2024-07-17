import secrets #used to import token_hex for random numbers/alphetic
import os
from PIL import Image #used to resize pic. from the pip install Pillow
from flask import render_template, url_for, flash, redirect, request, abort #request is a query parameter
from thoughts_guru import app, db, bcrypt, mail
from thoughts_guru.form import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm#for forms
from thoughts_guru.models import User, Post #for database settings
from flask_login import login_user, current_user, logout_user, login_required
#loggin user,check if the current user is logged in,logout user, allow user access a page only when loggedin
from flask_mail import Message

@app.route("/", strict_slashes = False)
def index():
    '''my home route rendering the content of my home page'''
    return render_template("index.html")

@app.route("/home", strict_slashes = False)
def home():
    '''my home route rendering the content of my home page'''
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("home.html", posts= posts)

@app.route("/about", strict_slashes = False)
def about():
    '''my about page route rendering content of the about page'''
    return render_template("about.html", title = "About")

@app.route("/register", strict_slashes = False, methods=['GET','POST'])
def register():
    '''this page render the registration page.'''
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():# confirm if the form was valid after submission
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        #the hashed password keeps your password coded incase of any attach of your database
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)#pushing into database
        db.session.add(user)
        db.session.commit()
        flash('Account has been created. You can now Login', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title = "Register", form = form)

@app.route("/login", strict_slashes = False, methods=['GET', 'POST'])
def login():
    '''gives access to the login page and allow user to login'''
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user,remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'You have successfully logged In', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))    
        else:
            flash(f'Enter the correct email and password', 'danger')
    return render_template("login.html", title = "Login", form = form)

@app.route("/logout", strict_slashes = False)
def logout():
    logout_user() # log out user from an account
    return redirect(url_for('home'))
    
def save_picture(form_picture):
    '''Used to save pictures uploaded in our profile picture'''
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename) # to split the filename from the file extention
    picture_fn = random_hex + f_ext
    pic_path = os.path.join(app.root_path, 'static/profile_pic/' + picture_fn)#join the path all the way to our package dirctory with static folder
    
    '''resize our picture using Image from Pillow'''
    p_size = (125,125)
    ima = Image.open(form_picture)
    ima.thumbnail(p_size)
    ima.save(pic_path)
    ###form_picture.save(pic_path)
    
    return picture_fn  #picture filename

@app.route("/account", strict_slashes = False, methods =['GET','POST'])
@login_required #this decorator shows that we need to login to access this route. we also need to show it where the login is located
def account():
    '''returns the account detail of individual user'''
    form = UpdateAccountForm()
    if form.validate_on_submit():
        '''updating users account in the database using a post method'''
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        '''filling in user info if it was a get request'''
        form.username.data =  current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pic/' + current_user.image_file)#add default image
    return render_template("account.html", title = "Account", image_file = image_file, form = form)

@app.route("/post/new", strict_slashes = False, methods = ['GET', 'POST'])
@login_required
def new_post():
    '''
        creating a new post which will e saved in the database
    '''
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title = form.title.data, content = form.content.data, author = current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title = 'New Post', form = form, legend = 'New Post')

@app.route("/post/<int:post_id>", strict_slashes = False)
def post(post_id):
    '''
        get a post from the database using the post id.
    '''    
    #post = Post.query.get(post_id)
    post = Post.query.get_or_404(post_id) # this get the post or return a 404 error message
    return render_template('post.html', title = post.title, post = post)

@app.route("/post/<int:post_id>/update", strict_slashes = False, methods = ['POST', 'GET'])
def update_post(post_id):
    '''To update a current post which has the post.id = post_id provided the user is the one wrote the post'''
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('post', post_id = post.id))
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title = 'Update Post', form =form, legend = 'Update Post')

@app.route("/post/<int:post_id>/delete", methods = ['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('You have successfully deleted the post', 'success')
    return redirect(url_for('home'))  

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender ='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token = token, _external=True)}
    
    If you did not make this request then simply ignore this email and no changes will be made.    
    '''
    mail.send(msg)

@app.route("/reset_password", methods = ['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to rest your password', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title = 'Reset Password', form =form)

@app.route("/reset_password/<token>", methods = ['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():# confirm if the form was valid after submission
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        #the hashed password keeps your password coded incase of any attach of your database
        user.password =hashed_password
        db.session.commit()
        flash('Your password has been updated. You can now Login', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title = 'Reset Password', form =form)
