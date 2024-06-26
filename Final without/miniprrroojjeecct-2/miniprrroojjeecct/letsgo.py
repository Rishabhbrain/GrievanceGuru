from gensim.models import Word2Vec,KeyedVectors
from flask import Flask, render_template, request
import nltk
from nltk.corpus import stopwords
import gensim.downloader as api

wv=api.load('word2vec-google-news-300')
# Download necessary NLTK resources (comment out if already downloaded)
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
    "Other": [],  # Catch-all category for unclassified grievances
}
def preprocess_text(text):
    text = text.lower()  # Convert to lowercase
    text = nltk.word_tokenize(text)  # Tokenize into words
    stop_words = set(stopwords.words("english"))  # Remove stop words
    text = [word for word in text if word not in stop_words]
    return text


def categorize_grievance(processed_text, grievance_categories, wv):
    words_in_text = processed_text.split()  # Split processed_text into individual words

    for category in grievance_categories:
        keywords = grievance_categories[category]
        for keyword in keywords:
            for word in words_in_text:
                try:
                    similarity_score = wv.similarity(keyword, word)
                    if similarity_score > 0.40:
                        return category
                except KeyError:
                    # Handle the case where the word or keyword is not in the vocabulary
                    pass

            # Check if the keyword is directly in the processed text
            if keyword in processed_text:
                return category

    return None
from pymongo import MongoClient
import warnings
import cryptography
from cryptography import x509

warnings.filterwarnings("ignore", category=cryptography.utils.CryptographyDeprecationWarning)



def insert_data(name,type):
    client = MongoClient(
        'mongodb+srv://asbaathakur:12345@case.3w4eqvk.mongodb.net/?retryWrites=true&w=majority&appName=Case')

    db = client['Cases']

    collection = db['Details']

    document = {"name": name,
                "Type": type

                }

    insert_doc = collection.insert_one(document)

    print(f"Inaerted Document successfully ID:{insert_doc.inserted_id} ")
    client.close()

x="harshit"

sentence="he took my umbrella without my permission"
preprocess_text(sentence)
category=categorize_grievance(sentence,grievance_categories,wv)
insert_data(x,category)


from flask import Flask,render_template, request, redirect, url_for

app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    data = request.form['data']
    processed_text = preprocess_text(data)
    category = categorize_grievance(processed_text, grievance_categories, wv)
    insert_data(name, category)
    return redirect(url_for('index'))


if __name__=="__main__":
    app.run(debug=True)
