from flask import Flask, render_template, request, url_for, redirect, abort, jsonify, flash
from flask import send_from_directory
import psycopg2
import os


class User:

    def __init__(self, login, password, user_order, image_link='/uploads/User_icon_2.png'):
        self.login = login
        self.password = password
        self.image_link = image_link
        self.user_order = user_order


app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/user/create', methods=['POST'])
def create_user():
    login = request.form['login']
    password = request.form['password']

    connection, cursor = get_connection()

    cursor.execute('''INSERT INTO USERS(login, password) VALUES (%s, %s);''', (login, password))

    connection.commit()

    close_connection(connection, cursor)
    return redirect(url_for('index'))


@app.route('/user/create/mob', methods=['POST'])
def create_user_mob():
    json = request.json
    login = json['login']
    password = json['password']

    connection, cursor = get_connection()
    try:
        cursor.execute('''INSERT INTO USERS(login, password) VALUES (%s, %s);''', (login, password))

        connection.commit()
    except Exception:
        return abort(400, 'Login must be unique')
    finally:
        close_connection(connection, cursor)

    return jsonify(success='ok')


@app.route('/user/all')
@app.route('/user/<int:user_id>')
def get_user(user_id=None):
    connection, cursor = get_connection()

    if user_id is None:
        cursor.execute('''SELECT login, password, user_order, image_link FROM USERS''')
        users_data = cursor.fetchall()

        close_connection(connection, cursor)

        return [User(i[0], i[1], i[2], i[3]).__dict__ for i in users_data]

    cursor.execute('''SELECT login, password, user_order, image_link FROM USERS
     WHERE user_order=%s''', [user_id])

    user_data = cursor.fetchall()

    close_connection(connection, cursor)

    if user_data.__len__() == 0:
        return abort(404, f"User with id {user_id} not found")
    # [['login', 'password']]
    return User(user_data[0][0], user_data[0][1], user_data[0][2], user_data[0][3]).__dict__


UPLOAD_FOLDER = './files'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/files')
def files():
    return render_template('file_form.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/files/add', methods=['POST'])
def add_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('files'))
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        print("OK")
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('download_file', name=filename))
    return redirect(url_for('files'))


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


def get_connection():
    connection = psycopg2.connect(database="users_application", user="administrator", password="root", host="localhost",
                                  port="5432")

    cursor = connection.cursor()

    return connection, cursor


def close_connection(conn, cur):
    conn.close()
    cur.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
