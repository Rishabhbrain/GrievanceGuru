from flask import Flask, render_template
from user import routes

tester = Flask(__name__)

@tester.route('/')
def home():
    return render_template('dashboard.html')

@tester.route('/dashboard/')
def dashboard():
    return render_template('base.html')

if __name__ == '__main__':
    tester.run(debug=True)
