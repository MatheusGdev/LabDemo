from flask import Flask, render_template, redirect, url_for, request, session
from flask_mysqldb import MySQL
import hashlib
import MySQLdb.cursors
import re
import time

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'pizza'

# Enter your database connection details below
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'webappuser'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'webappdb'

# Intialize MySQL
mysql = MySQL(app)

# use decorators to link the function to a url
@app.route('/')
def home():
    return redirect(url_for('login'))

# http://localhost:5000/login/ - this will be the login page, we need to use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = 'Please Log In'
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in users table in our database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['admin'] = account['admin']
            # Redirect to home page
            if session['admin']:
                return redirect(url_for('adminhome'))
            else:
                return redirect(url_for('userhome'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg=msg)

# http://localhost:5000/login/logout - this will be the logout page
@app.route('/login/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('admin', None)
    # Redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/login/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/login/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = 'Sign up!'
    # Check if "username", "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        email = request.form['email']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', [username])
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM users WHERE email = %s', [email])
        emailUsed = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif emailUsed:
            msg = 'Email already in use!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists, email is not in use, and the form data is valid. insert new user into users table
            cursor.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'        
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/login/resetpass - this will be the registration page, we need to use both GET and POST requests
@app.route('/login/resetpass', methods=['GET', 'POST'])
def resetpass():
    # Output message if something goes wrong...
    msg = 'Enter your Email'
    # Check if "email" entered on form
    if request.method == 'POST' and 'email' in request.form:
        # Create variables for easy access
        email = request.form['email']
        resetpass = hashlib.sha256('reset'.encode()).hexdigest()

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', [email])
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            cursor.execute("UPDATE users SET password=%s WHERE email=%s", [resetpass, email])
            mysql.connection.commit()
            msg = 'Password Reset'
        else:
            msg = 'Password not Reset. Account does not exist.'        
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please enter your email!'
    # Show registration form with message (if any)
    return render_template('resetpass.html', msg=msg)

# http://localhost:5000/login/userhome - this will be the user home page, only accessible for loggedin users
@app.route('/login/userhome')
def userhome():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the user home page
        return render_template('userhome.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/login/adminhome - this will be the admin home page, only accessible for loggedin admins
@app.route('/login/adminhome')
def adminhome():
    # Check if user is loggedin
    if 'loggedin' in session and session['admin']:
        # admin is loggedin show them the admin home page
        return render_template('adminhome.html', username=session['username'])
    # admin is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/login/profile - this will be the profile page, only accessible for loggedin users
@app.route('/login/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM users WHERE id = %s', [session['id']])
        mysql.connection.commit()
        return redirect(url_for('logout'))

    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/login/netaccrequest', methods=['GET', 'POST'])
def netaccrequest():
    # Show admin page (list requests)
    if session['admin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT users.id, users.username, netaccrequests.status FROM users, netaccrequests WHERE users.id = netaccrequests.userid')
        data = cursor.fetchall()

        return render_template('existingrequests.html', data=data)  
    
    # Not admin
    else:
        # Create variables for easy access
        userid = session['id']
    
        # Check if request already exists for this user
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM netaccrequests where userid = %s', [userid])
        userrequest = cursor.fetchone()

        # If request already exists for this user
        if userrequest:
            return render_template('requestnotsubmitted.html', data=userrequest)

        # Request doesn't exist. Allow user to submit new request
        else:
            if request.method == 'POST':
                # Request does not currently exist. Create one.
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO netaccrequests (userid) VALUES (%s)', [userid])
                mysql.connection.commit()
                time.sleep(5)
                # return render_template('requestnotsubmitted.html', data=status)
                
            return render_template('netaccrequest.html')

@app.route('/login/approverequest', methods=['GET', 'POST'])
def approverequest():
    if request.method == 'POST' and 'RequestUserId' in request.form:
        netaccuserid = request.form['RequestUserId']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE netaccrequests SET status='APPROVED' WHERE userid=%s", [netaccuserid])
        mysql.connection.commit()
    
    return redirect(url_for('netaccrequest'))

@app.route('/login/denyrequest', methods=['GET', 'POST'])
def denyrequest():
    if request.method == 'POST' and 'RequestUserId' in request.form:
        netaccuserid = request.form['RequestUserId']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE netaccrequests SET status='DENIED' WHERE userid=%s", [netaccuserid])
        mysql.connection.commit()
    
    return redirect(url_for('netaccrequest'))

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',ssl_context=('cert.pem', 'key.pem'))
