from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from mysql_db import MySQL
import mysql.connector

app = Flask(__name__)

application = app

app.config.from_pyfile('config.py')

db = MySQL(app)

from auth import bp_auth, check_rights, init_login_manager
from visits import bp_visit

app.register_blueprint(bp_auth)
app.register_blueprint(bp_visit)
app.jinja_env.globals.update(current_user=current_user)

init_login_manager(app)


@app.before_request
def journal():
    query = '''
        INSERT INTO `visit_logs` (path, id_user) VALUES (%s, %s)
    '''
    try:
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query, (request.path, getattr(current_user, "id", None)))
        db.connection().commit()
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()


def get_roles():
    query = 'SELECT * FROM roles'
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query)
    roles = cursor.fetchall()
    cursor.close()
    return roles


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/users/')
@login_required
def show_users():
    query = '''
        SELECT users.*, roles.name as role_name
        FROM users
        LEFT JOIN roles
        on roles.id = users.id_role
        '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()
    return render_template('users/index.html',users=users)


@app.route('/users/create', methods = ['POST', 'GET'])
@login_required
@check_rights('create')
def create():
    roles = get_roles()
    if request.method == 'POST':
        login = request.form['login']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        password = request.form['oldpassword']
        id_role = request.form['id_role']
        try:
            query = '''
                insert into users (login, last_name, first_name, middle_name, password_hash, id_role)
                VALUES (%s, %s, %s, %s, SHA2(%s, 256), %s)
                '''
            cursor = db.connection().cursor(named_tuple=True)
            cursor.execute(query, (login, last_name, first_name, middle_name, password, id_role))
            db.connection().commit()
            flash(f'Новый пользователь {login} заспавнился успешно', 'success')
            cursor.close()
        except mysql.connector.errors.DatabaseError:
            db.connection().rollback()
            flash(f'Упс! Тут ошибка при создании пользователя', 'danger')
            return render_template('users/create.html')

    return render_template('users/create.html', roles=roles)


@app.route('/users/show/<int:id_user>')
@login_required
@check_rights('show')
def show_user(id_user):
    query = 'SELECT users.*, roles.name AS role_name FROM users LEFT JOIN roles ON users.id_role = roles.id WHERE users.id=%s'
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query, (id_user,))
    user = cursor.fetchone()
    cursor.close()
    return render_template('users/show.html', user=user)


@app.route('/users/edit/<int:id_user>', methods=["POST", "GET"])
@check_rights('edit')
def edit(id_user):
    roles = get_roles()
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        try:
            if current_user.is_admin():
                id_role = request.form['id_role']
                query = '''
                    UPDATE users set first_name = %s, last_name = %s, middle_name = %s, id_role = %s where id = %s
                    '''
                cursor = db.connection().cursor(named_tuple=True)
                cursor.execute(query, (first_name, last_name, middle_name, id_role, id_user))
                db.connection().commit()
            else:
                query = '''
                    UPDATE users set first_name = %s, last_name = %s, middle_name = %s where id = %s
                    '''
                cursor = db.connection().cursor(named_tuple=True)
                cursor.execute(query, (first_name, last_name, middle_name, id_user))
                db.connection().commit()
            flash(f'Данные пользователя {first_name} успешно обновлены.', 'success')
            cursor.close()
        except mysql.connector.errors.DatabaseError:
            db.connection().rollback()
            flash(f'При обновлении пользователя произошла ошибка.', 'danger')
            return render_template('users/edit.html')

    query = '''
        SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles on roles.id = users.id_role where users.id=%s
        '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query, (id_user,))
    user = cursor.fetchone()
    cursor.close()
    return render_template('users/edit.html', user=user, roles=roles)

@app.route('/users/delete/')
@check_rights('delete')
def delete():
    try:
        id_user = request.args.get('id_user')
        query_logs = '''
            DELETE FROM visit_logs WHERE id_user = %s
            '''
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query_logs, (id_user,))
        query = '''
            DELETE FROM users where id = %s
            '''
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query, (id_user,))
        db.connection().commit()
        flash(f'Данный пользователь {id_user} успешно вынесен из мира сего', 'success')
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()
        flash(f'При вынесении данного пользователя из мира сего произошла ошибка', 'danger')
        return render_template('users/index.html', id_user=id_user)

    return redirect(url_for('show_users'))
