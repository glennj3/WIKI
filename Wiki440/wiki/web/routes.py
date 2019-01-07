"""
    Routes
    ~~~~~~
"""
import os
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import send_from_directory
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from werkzeug.utils import secure_filename

from wiki.core import Processor
from wiki.web.forms import EditorForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web.forms import RegisterForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect
from wiki.web.user import UserManager
from config import UPLOAD_FOLDER, USER_DIR
from wiki.web.forms import profileeditForm
from wiki.web.user import allowed_file

bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')

"""
The upload route is for submitting files to a folder, upload folder.
If there is a file and it is allowable in "ALLOWED_EXTENSIONS" in config.py, then
it will be uploaded to the folder. 
"""
@bp.route('/upload/', methods=['GET', 'POST'])
@protect
def upload_file():
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash('Upload Successful')
            return redirect(url_for('wiki.upload_file', file=filename))
    return render_template('upload.html')

"""
This route returns the specified file in the path.
It is used in the download page so a user may download an uploaded file.
"""
@bp.route('/uploads/<path:filename>')
@protect
def uploads(filename):
    return send_from_directory(UPLOAD_FOLDER,
                               filename, as_attachment=True)


"""
Register route is a form which utilizes USERMANAGER, to create
USER objects and write them to the JSON file users.json. If registration
was successful, it will redirect to the login screen. The page returned is
the register.html page.
"""
@bp.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        UserManager(USER_DIR).add_user(username, password)
        flash('Registered Successfully. Please Log in.', 'success')
        return redirect(url_for('wiki.user_login'))
    return render_template('register.html', form=form)

"""
Downloads lists the files in the UPLOAD_FOLDER directory and 
presents them in the downloads.html for download in a list of clickable links.
"""
@bp.route('/downloads/')
@protect
def downloads():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('downloads.html', files=files)

@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))

"""
The profile route returns either the profile of the user, if they just go the the
profile url, or if specified in the url they can view other users profiles as well.
Only their own profile is editable.
"""
@bp.route('/profile/<string:username>')
@bp.route('/profile/')
@protect
def profile(username=""):
    if username == "":
        user = UserManager(USER_DIR).get_user(current_user.name)
        username=user.name
    else:
        user = UserManager(USER_DIR).get_user(username)
    userdata = user.get('ProfileData')
    currentBool = False
    if user.name == current_user.name:
        currentBool=True
    if username is None:
        return render_template("404.html"),404
    else:
        return render_template('profile.html',username=username, userdata=userdata, currentBool=currentBool)

"""
Profile edit allows the user to edit their profile data in the JSON, "profileData" dictionary. 
This only applies if it is their own profile.
"""
@bp.route('/profile/edit', methods=['GET', 'POST'])
@protect
def profileedit():
    form = profileeditForm()
    if form.validate_on_submit():
        user = UserManager(USER_DIR).get_user(current_user.name)
        user.set("ProfileData",{"Location": form.location.data, "Bio": form.bio.data, "Gender": form.gender.data, "Speciality": form.speciality.data, "Picture": "Default.jpg"})
        flash('Edit Successful.', 'success')
        return redirect(url_for('wiki.profile',username=current_user.name))
    return render_template('profileedit.html', form=form)

@bp.route('/user/')
def user_index():
    pass


@bp.route('/user/create/')
def user_create():
    pass


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
