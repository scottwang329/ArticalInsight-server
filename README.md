# brains

Here lives the server of Truth Be Told

## Running Locally

Making sure python 3.7 is installed in your computer

Set up your virtual environment:

    virtualenv env

Enter your virtual environment:

    source env/bin/activate

Install dependencies:

    pip install -r requirements.txt

Provide authentication credentials to your application code by setting the environment variable GOOGLE_APPLICATION_CREDENTIALS

export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"

About how to use the [Google Cloud Natural Language API] please visit https://cloud.google.com/natural-language/.

Test your application locally:

    python main.py
