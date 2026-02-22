from flask import Flask, render_template
from models import db
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basement_stacks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def welcome():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
