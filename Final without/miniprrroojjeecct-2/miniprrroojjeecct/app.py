from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, session
from gensim.models import KeyedVectors
import nltk
from nltk.corpus import stopwords
import gensim.downloader as api
from pymongo import MongoClient
import warnings
import cryptography
from cryptography import x509
import pyrebase
import os

app = Flask(__name__)
config = {
    'apiKey': "AIzaSyANYq3vNQhStKalhZ300KL-w2ib1aqQ4Nw",
    'authDomain': "miniproject-53f14.firebaseapp.com",
    'projectId': "miniproject-53f14",
    'storageBucket': "miniproject-53f14.appspot.com",
    'messagingSenderId': "585275365596",
    'appId': "1:585275365596:web:8ec488013314d43f2f3c19",
    'measurementId': "G-7QRRLMWVJF",
    'databaseURL': ''
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

app.secret_key = 'secret'

# Load word2vec model
wv = api.load('word2vec-google-news-300')



warnings.filterwarnings("ignore", category=cryptography.utils.CryptographyDeprecationWarning)

grievance_categories = {
    "Theft": [
        "steal",
        "stolen",
        "rob",
        "robbery",
        "burglary",
        "larceny",
        "pickpocket",
        "embezzle",
        "pilfer",
        "approval",
    ],
    "Harassment": [
        "harass",
        "harassed",
        "bullying",
        "threat",
        "intimidate",
        "stalk",
        "abuse",
        "offensive",
    ],
    "Discrimination": [
        "discriminate",
        "discrimination",
        "bias",
        "prejudice",
        "unequal",
        "unfair",
        "segregation",
    ],
    "Fraud": [
        "fraud",
        "scam",
        "con",
        "deception",
        "embezzlement",
        "misrepresentation",
        "forgery",
    ],
    "Vandalism": [
        "vandalize",
        "vandalism",
        "deface",
        "destroy",
        "damage",
        "graffiti",
        "tamper",
    ],
    "Other": [],
}

def preprocess_text(text):
    text = text.lower()
    tokens = nltk.word_tokenize(text)
    stop_words = set(stopwords.words("english"))
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

def categorize_grievance(processed_text, grievance_categories, wv):
    words_in_text = processed_text.split()
    for category, keywords in grievance_categories.items():
        for keyword in keywords:
            for word in words_in_text:
                try:
                    similarity_score = wv.similarity(keyword, word)
                    if similarity_score > 0.40:
                        return category
                except KeyError:
                    pass
            if keyword in processed_text:
                return category
    return "Other"

def insert_data(name, category):
    client = MongoClient(
        'mongodb+srv://asbaathakur:12345@case.3w4eqvk.mongodb.net/?retryWrites=true&w=majority&appName=Case'
    )
    db = client['Cases']
    collection = db['Details']
    document = {"name": name, "Type": category, "completed": False}  # Initially set as not completed
    insert_doc = collection.insert_one(document)
    inserted_id = insert_doc.inserted_id  # Get the inserted _id
    print(f"Inserted Document successfully ID: {inserted_id}")
    client.close()
    return inserted_id

def fetch_all_data():
    client = MongoClient(
        'mongodb+srv://asbaathakur:12345@case.3w4eqvk.mongodb.net/?retryWrites=true&w=majority&appName=Case'
    )
    db = client['Cases']
    collection = db['Details']
    documents = list(collection.find())
    for doc in documents:
        doc['_id'] = str(doc['_id'])
    return documents

def fetch_data_by_id(case_id):
    client = MongoClient(
        'mongodb+srv://asbaathakur:12345@case.3w4eqvk.mongodb.net/?retryWrites=true&w=majority&appName=Case'
    )
    db = client['Cases']
    collection = db['Details']
    try:
        document = collection.find_one({"_id": ObjectId(case_id)}, {"name": 1, "Type": 1, "completed": 1})
        if document:
            document['_id'] = str(document['_id'])
        return document
    except:
        return None

def fetch_user_cases(user_id):
    client = MongoClient(
        'mongodb+srv://asbaathakur:12345@case.3w4eqvk.mongodb.net/?retryWrites=true&w=majority&appName=Case'
    )
    db = client['Cases']
    collection = db['Details']
    user_cases = list(collection.find({"user_id": user_id}))
    for case in user_cases:
        case['_id'] = str(case['_id'])  # Convert ObjectId to string for rendering
    client.close()
    return user_cases

@app.route('/')
def index():
    search_result = None
    if 'search_id' in request.args:
        case_id = request.args.get('search_id')
        search_result = fetch_data_by_id(case_id)
        if search_result:
            # If search result is found, render full template with search result
            return render_template('index.html', search_result=search_result)

    # If no search result or search query, render minimal template without cases
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    data = request.form['grievance']
    processed_text = preprocess_text(data)
    category = categorize_grievance(processed_text, grievance_categories, wv)
    inserted_id = insert_data(name, category)  # Get the inserted _id

    # Create a grievance ticket
    ticket_content = f"Name: {name}\nGrievance: {data}\nCategory: {category}\nID: {inserted_id}"
    ticket_file = f"static/tickets/{name}_ticket.txt"

    if not os.path.exists('static/tickets'):
        os.makedirs('static/tickets')

    with open(ticket_file, "w") as file:
        file.write(ticket_content)

    ticket_url = url_for('static', filename=f"tickets/{name}_ticket.txt", _external=True)
    mailto_link = f"mailto:dbmsaum@gmail.com?subject=Grievance%20Ticket&body={ticket_url}"

    return render_template('result.html', grievance=data, category=category, ticket_url=ticket_url,
                           mailto_link=mailto_link, inserted_id=inserted_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = email
            return redirect('/admin')
        except:
            return 'Failed to login'
    return render_template('login.html')

@app.route('/admin')
def admin():
    if 'user' in session:
        data = fetch_all_data()
        return render_template('admin.html', data=data)
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')

@app.route('/complete/<id>')
def mark_as_complete(id):
    client = MongoClient(
        'mongodb+srv://asbaathakur:12345@case.3w4eqvk.mongodb.net/?retryWrites=true&w=majority&appName=Case'
    )
    db = client['Cases']
    collection = db['Details']
    collection.update_one({"_id": ObjectId(id)}, {"$set": {"completed": True}})
    client.close()
    return redirect(url_for('admin'))

@app.route('/incomplete/<id>')
def mark_as_incomplete(id):
    client = MongoClient(
        'mongodb+srv://asbaathakur:12345@case.3w4eqvk.mongodb.net/?retryWrites=true&w=majority&appName=Case'
    )
    db = client['Cases']
    collection = db['Details']
    collection.update_one({"_id": ObjectId(id)}, {"$set": {"completed": False}})
    client.close()
    return redirect(url_for('admin'))

@app.route('/search', methods=['GET'])
def search():
    case_id = request.args.get('search_id')
    search_result = fetch_data_by_id(case_id)
    return render_template('index.html', search_result=search_result)

if __name__ == '__main__':
    app.run(debug=False)

