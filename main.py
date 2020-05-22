from flask import Flask, redirect, render_template, request

from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from google.protobuf.json_format import MessageToDict, MessageToJson
from flask_cors import CORS
import requests
import yaml
import json
from newspaper import Article

app = Flask(__name__)
CORS(app)


@app.route('/')
def homepage():
    # Return a Jinja2 HTML template of the homepage.
    return render_template('homepage.html')


@app.route('/run_language', methods=['GET', 'POST'])
def run_language():
    # Create a Cloud Natural Language client
    client = language.LanguageServiceClient()

    # Retrieve inputted text from the form and create document object
    text = request.form['text']
    document = types.Document(
        content=text, type=enums.Document.Type.PLAIN_TEXT)

    # Retrieve response from Natural Language API's analyze_entities() method
    response = client.analyze_entities(document)
    entities = response.entities

    # Retrieve response from Natural Language API's analyze_sentiment() method
    response = client.analyze_sentiment(document)
    sentiment = response.document_sentiment

    # Retrieve category and confidence level
    response = client.classify_text(document)
    categories = response.categories

    result = {}
    for category in categories:
        # Turn the categories into a dictionary of the form:
        # {category.name: category.confidence}, so that they can
        # be treated as a sparse vector.
        result[category.name] = category.confidence
    print(text)
    for category in categories:
        text = text + 'category: ' + category.name
        text = text + 'confidence: ' + str(category.confidence)

    # Return a Jinja2 HTML template of the homepage and pass the 'text', 'entities',
    # and 'sentiment' variables to the frontend. These contain information retrieved
    # from the Natural Language API.
    return render_template('homepage.html', text=text, entities=entities, sentiment=sentiment)


def analyze(articletext):
    # Create a Cloud Natural Language client
    client = language.LanguageServiceClient()

    document = types.Document(
        content=articletext, type=enums.Document.Type.PLAIN_TEXT)

    # Retrieve response from Natural Language API's analyze_entities() method
    response_entities = client.analyze_entities(document)

    top_three_keywords = MessageToDict(response_entities)

    top_three_keywords_array = []

    for i in range(0, 3):
        top_three_keywords_array.append(top_three_keywords["entities"][i]["name"])

    # Retrieve response from Natural Language API's analyze_sentiment() method
    response_sentiment = client.analyze_sentiment(document)

    # Retrieve category and confidence level
    response_categories = client.classify_text(document)

    sentiment = MessageToDict(response_sentiment)["documentSentiment"]
    categories = MessageToDict(response_categories)["categories"]

    return json.dumps({'topthreekeywords': top_three_keywords_array, 'sentiment': sentiment, 'categories': categories})


@app.route('/fact_check', methods=['GET', 'POST'])
def check():
    with open(r'config.yaml') as file:
        documents = yaml.load(file)
    URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    PARAMS = {'query': request.form['text'], 'key': documents['google_key']}
    HEADERS = {"X-Referer": "https://explorer.apis.google.com"}

    response = requests.get(url=URL, params=PARAMS, headers=HEADERS).json()
    ret = {}
    ret['results'] = [{'factRatings': item['claimReview'][0]}
                      for item in response['claims']]
    ret_cleaned = {}
    ret_cleaned["results"] = [{'truthRating': item['factRatings']['textualRating'],
                               'url': item['factRatings']['url']} for item in ret['results']]

    return json.dumps(ret_cleaned)


@app.route('/scrap_website', methods=['GET', 'POST'])
def scrapwebsite():
    url = request.form['url']
    articletext = parse_text_from_url(url)
    return analyze(articletext)


@app.errorhandler(500)
def server_error(e):
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


def parse_text_from_url(NEWS_URL):
    url = NEWS_URL
    article = Article(url)
    article.download()
    article.parse()
    return article.text


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
