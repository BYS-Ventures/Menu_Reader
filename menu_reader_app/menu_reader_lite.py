#app.py
from flask import Flask, flash, request, redirect, url_for, render_template, session, jsonify
import os
import requests
import json
import pickle
import numpy as np

app = Flask(__name__)

app.secret_key = "secret key"

THUMBNAILS_FOLDER = 'static/thumbnails/'
UPLOAD_FOLDER = 'static/uploads/'

# Set base path to locate files in the correct directory
base_path = os.path.dirname(__file__)
file_images_path = os.path.join(base_path, 'file_images.pkl')
file_dimensions_path = os.path.join(base_path, 'file_dimensions.pkl')

# Load the pickle files
file_images = pickle.load(open(file_images_path, "rb"))
file_dimensions = pickle.load(open(file_dimensions_path, "rb"))

# Load models once at startup
model_path = os.path.join(base_path, 'menu_function', 'MyFunction')
xgb = pickle.load(open(os.path.join(model_path, 'xgb.pkl'), 'rb'))
xgb2_4 = pickle.load(open(os.path.join(model_path, 'xgb2_4.pkl'), 'rb'))
xgb2_5 = pickle.load(open(os.path.join(model_path, 'xgb2_5.pkl'), 'rb'))

# Ensure required folders exist
os.makedirs(os.path.join(base_path, THUMBNAILS_FOLDER), exist_ok=True)
os.makedirs(os.path.join(base_path, UPLOAD_FOLDER), exist_ok=True)

app.config['THUMBNAILS_FOLDER'] = THUMBNAILS_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

# Predefined thumbnails
thumbnails = ['parkers_menu.jpeg', 'aubrees_menu.jpeg', 'meatheads_menu.jpeg', 'portillos_menu.jpeg', 'roanoke_menu.jpeg']

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.int64):
            return int(obj)
        return super(NumpyEncoder, self).default(obj)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_filename(file_path):
    return os.path.basename(file_path)  # Use only the filename without any path

@app.route('/')
def home():
    return render_template('index.html', thumbnails=thumbnails)

@app.route('/display/<filename>')
def display_image(filename):
    if filename in thumbnails:
        session['image_source'] = 'thumbnails'
    else:
        session['image_source'] = 'uploads'

    source = session.pop('image_source', 'uploads')  # default to 'uploads' if not set and pop it

    if source == 'uploads':
        return render_template('index.html', filename='uploads/' + filename, thumbnails=thumbnails)
    else:
        session['image_source'] = 'thumbnails'
        session.pop('selected_filename', None)
        session['selected_filename_path'] = THUMBNAILS_FOLDER + filename
        return render_template('index.html', filename='thumbnails/' + filename, thumbnails=thumbnails)

@app.route('/display/menu_read', methods=['GET', 'POST'])
def new_function():
    file_path = session.get('selected_filename_path')
    filename = extract_filename(file_path)

    try:
        result = file_images.get(filename)

        # Check if dimensions are available
        dimensions = file_dimensions.get(filename)
        if dimensions is not None:
            height_img, width_img = dimensions
        else:
            # Handle missing dimensions
            flash(f"Error: No dimensions found for {filename}")
            return render_template('index.html', thumbnails=thumbnails, filename=filename)

        data = {
            "result": result,
            "height_img": height_img,
            "width_img": width_img
        }

        # Directly call the function without an HTTP request
        response = my_function_internal(data)

        if 'error' in response:
            flash(f"Error: {response['error']}")
            return render_template('index.html', thumbnails=thumbnails, filename=filename)

        categories = response
        return render_template('index.html', categories=categories, thumbnails=thumbnails, filename=filename)

    except Exception as e:
        flash(f"Error: {e}")
        print('Error: ', e)
        return render_template('index.html', thumbnails=thumbnails, filename=filename)

# Internal function for prediction
def my_function_internal(data):
    try:
        # Placeholder logic for prediction (update as needed)
        result = {
            'xgb_prediction': xgb.predict(data['result']),
            'xgb2_4_prediction': xgb2_4.predict(data['result']),
            'xgb2_5_prediction': xgb2_5.predict(data['result']),
        }
        return result

    except Exception as e:
        return {'error': str(e)}

# New API endpoint to handle function requests
@app.route('/api/MyFunction', methods=['POST'])
def my_function():
    try:
        # Get the data from the request
        data = request.get_json()
        return jsonify(my_function_internal(data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)
