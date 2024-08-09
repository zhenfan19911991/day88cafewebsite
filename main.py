from flask import Flask, abort, render_template, redirect, url_for, flash, request, session
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from forms import RegisterForm, LoginForm, CreateCafeForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from selenium import webdriver
import time
import re as regex_f

app = Flask(__name__)
Bootstrap5(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy()
db.init_app(app)

with app.app_context():
    Ba = automap_base()

class Cafe(Ba):
    __tablename__= 'cafe'
    mapurl_collection = db.relationship('MapUrl', back_populates="cafe_collection", uselist=False)

class MapUrl(Ba):
    __tablename__ = "mapurl"

    cafe_id = db.Column(db.Integer, db.ForeignKey('cafe.id'), nullable=False)
    cafe_collection = db.relationship('Cafe', back_populates="mapurl_collection")

with app.app_context():
    Ba.prepare(autoload_with = db.engine)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

with app.app_context():
    db.create_all()


# with app.app_context():
#     result1 = db.session.execute(db.select(Cafe).where(Cafe.name == 'Forage Cafe')).scalar()
#     result1.img_url = 'https://media-cdn.tripadvisor.com/media/photo-s/1c/82/d1/d7/img-20210110-143349-largejpg.jpg'
#     result = db.session.execute(db.select(Cafe).where(Cafe.name == 'Science Gallery London')).scalar()
#     result.img_url = 'https://static1.squarespace.com/static/5dc192d42e6f762c2859d5cf/t/647f265f4d222c5cef557d62/1686054495914/NWP4205-optimised.jpg?format=1500w'
#     result2 = db.session.execute(db.select(Cafe).where(Cafe.name == 'FORA Borough')).scalar()
#     result2.img_url = 'https://flavourvenuesearch.com/wp-content/uploads/2020/03/ForaB1.jpg'
#     result3 = db.session.execute(db.select(Cafe).where(Cafe.name == 'The Peckham Pelican')).scalar()
#     result3.seats = '0-10'
#     db.session.commit()

# with app.app_context():
#     embed_url = db.session.execute(db.select(MapUrl).where(MapUrl.id == 22)).scalar()
#     db.session.delete(embed_url)
#     db.session.commit()
#
# with app.app_context():
#     embed_url = db.session.execute(db.select(MapUrl).where(MapUrl.cafe_id == 22)).scalar()
#     embed_url.id = 22
#     db.session.commit()
#
# with app.app_context():
#     embed_url = db.session.execute(db.select(MapUrl).where(MapUrl.cafe_id == 22)).scalar()
#     print(embed_url.id)


@app.route('/', methods = ['GET', 'POST'])
def home():
    cafes = db.session.query(Cafe).order_by(Cafe.coffee_price).all()
    count = db.session.query(Cafe).count()

    if request.method == 'POST':
        dic_result = request.form.to_dict()

        if 'seats' in dic_result.keys():
            dic_result.pop('seats')
        if 'coffee_price' in dic_result.keys():
            dic_result.pop('coffee_price')

        re = db.session.query(Cafe).filter_by(**dic_result)

        seat = request.form.getlist('seats')
        re_1 = re.filter(Cafe.seats.in_(seat))

        price = request.form.get('coffee_price')
        re_2 = re_1.filter(Cafe.coffee_price <= price).order_by(Cafe.coffee_price).all()
        count = re_1.filter(Cafe.coffee_price <= price).count()
        return render_template('index.html', cafes=re_2, count = count)
    return render_template('index.html', cafes = cafes, count = count)

@app.route('/map', methods = ['GET', 'POST'])
def home_map():
    key = request.args.get('id')
    cafe = db.session.execute(db.select(Cafe).where(Cafe.id == key)).scalar()
    embed_url = db.session.execute(db.select(MapUrl).where(MapUrl.cafe_id == key)).scalar()
    if embed_url:
        embed_link = embed_url.mapurl
    else:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(cafe.map_url)
        time.sleep(5)
        get_url = driver.current_url
        driver.quit()

        regex = r"@([0-9.-]+),([0-9.-]+),([0-9.-]+)"
        match = regex_f.search(regex, get_url)
        if match:
            latitude, longitude, zoom = match.groups()
            embed_link = f"https://maps.google.com/maps?q={latitude},{longitude}&z={zoom}&output=embed"
        else:
            embed_link = None
        new_map = MapUrl(
            cafe_id=cafe.id,
            mapurl=embed_link
        )
        db.session.add(new_map)
        db.session.commit()

    return render_template('index_map.html', cafe = cafe, link = embed_link)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if not user:
            hash_password = generate_password_hash(form.password.data)
            new_user = User(
                email=form.email.data,
                password=hash_password
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('You have successfully logged in.')
            return redirect(url_for('home'))
        else:
            flash('You have registered with this email. Please log in instead.')
            return redirect(url_for('login'))
    return render_template('register.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('You have successfully logged in.')
                return redirect(url_for('home'))
            else:
                flash('Wrong password. Please try again.')
                return redirect(url_for('login'))
        else:
            flash('You have not registered with this email. Please register first.')
            return redirect(url_for('register'))
    return render_template('login.html', form = form)

def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.email == 'abc@admin.com':
                return function(*args, **kwargs)
            else:
                flash('Only admin can access this page. Redirecting to home page')
                return abort(403)
        else:
            flash('You have not registered or logged in to the website. Redirecting to home page')
            return abort(403)
    return wrapper

@app.route('/logout')
@login_required
def logout():
    session.pop('_flashes', None)
    logout_user()
    return redirect(url_for('home'))

@app.route('/addcafe', methods = ['GET', 'POST'])
@admin_only
def addcafe():
    form = CreateCafeForm()
    if form.validate_on_submit():
        if form.has_sockets.data == 'Yes':
            has_sockets = 1
        else:
            has_sockets = 0

        if form.has_wifi.data == 'Yes':
            has_wifi = 1
        else:
            has_wifi = 0

        if form.has_toilet.data == 'Yes':
            has_toilet = 1
        else:
            has_toilet = 0

        if form.can_take_calls.data == 'Yes':
            can_take_calls = 1
        else:
            can_take_calls = 0

        new_cafe = Cafe(
            name = form.name.data,
            map_url = form.map_url.data,
            img_url = form.img_url.data,
            location = form.location.data,
            has_sockets = has_sockets,
            has_wifi = has_wifi,
            has_toilet = has_toilet,
            can_take_calls = can_take_calls,
            seats = form.seats.data,
            coffee_price = form.coffee_price.data
        )
        db.session.add(new_cafe)
        db.session.commit()
        flash('You have successfully added the new cafe.')
        return redirect(url_for("home"))
    return render_template('addcafe.html', form = form)

@app.route("/delete")
@admin_only
def delete_cafe():
    cafe_id = request.args.get('d_id')
    cafe_to_delete = db.get_or_404(Cafe, cafe_id)
    map_to_delete = db.get_or_404(MapUrl, cafe_id)
    db.session.delete(cafe_to_delete)
    db.session.delete(map_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/editcafe', methods = ['GET', 'POST'])
@admin_only
def editcafe():
    cafe_id = request.args.get('cafe_id')
    cafe = db.get_or_404(Cafe, cafe_id)
    if Cafe.has_sockets == 1:
        has_sockets = 'Yes'
    else:
        has_sockets = 'No'
    if Cafe.has_toilet == 1:
        has_toilet = 'Yes'
    else:
        has_toilet = 'No'

    if Cafe.has_wifi == 1:
        has_wifi = 'Yes'
    else:
        has_wifi = 'No'

    if Cafe.can_take_calls == 1:
        can_take_calls = 'Yes'
    else:
        can_take_calls = 'No'

    form = CreateCafeForm(
        name=cafe.name,
        map_url=cafe.map_url,
        img_url=cafe.img_url,
        location=cafe.location,
        has_sockets= has_sockets,
        has_wifi=has_wifi,
        has_toilet=has_toilet,
        can_take_calls=can_take_calls,
        seats=cafe.seats,
        coffee_price=cafe.coffee_price
    )
    if form.validate_on_submit():
        if form.has_sockets.data == 'Yes':
            has_sockets = 1
        else:
            has_sockets = 0
        if form.has_wifi.data == 'Yes':
            has_wifi = 1
        else:
            has_wifi = 0
        if form.has_toilet.data == 'Yes':
            has_toilet = 1
        else:
            has_toilet = 0
        if form.can_take_calls.data == 'Yes':
            can_take_calls = 1
        else:
            can_take_calls = 0

        cafe.name = form.name.data
        cafe.map_url = form.map_url.data
        cafe.img_url = form.img_url.data
        cafe.location = form.location.data
        cafe.has_sockets = has_sockets
        cafe.has_wifi = has_wifi
        cafe.has_toilet = has_toilet
        cafe.can_take_calls = can_take_calls
        cafe.seats = form.seats.data
        cafe.coffee_price = form.coffee_price.data
        db.session.commit()
        flash('You have successfully edited the new cafe.')
        return redirect(url_for("home"))
    return render_template("addcafe.html", form=form, is_edit=True)


if __name__ == "__main__":
    app.run()


