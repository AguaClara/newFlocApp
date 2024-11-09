import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from db import Image, Floc, DatabaseOperations, start
import base64
import os
import random
import size

# Set up app and database
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///floc.db"
db = SQLAlchemy(app)
CORS(app)

# Routes
@app.route("/upload", methods=["POST"])
def upload_image():
    body = json.loads(request.data)
    image_base64_data = body.get("image")
    filePath = body.get("filePath")

    filename_path = os.path.join(os.path.dirname(__file__), "filename.txt")

    if filePath is None and os.path.exists(filename_path):
        with open(filename_path, "r") as file:
            filePath = file.read().strip()
    elif filePath is None:
        return jsonify({"error": "No file path provided and filename.txt does not exist."}), 400

    with open(filename_path, "w") as file:
        file.write(filePath)

    session = start()
    db_ops = DatabaseOperations(session)
    current_id = db_ops.get_current_image_id()
    image_name = f"image{current_id + 1}" if current_id is not None else "image0"
    filePath = os.path.join(filePath, f"{image_name}.jpeg")

    if "," in image_base64_data:
        image_base64_data = image_base64_data.split(",")[1]
    image_data = base64.b64decode(image_base64_data)

    with open(filePath, "wb") as file:
        file.write(image_data)

    new_image = db_ops.add_image(image_name, image_base64_data)
    size_info = size.size_image(filePath, session, db_ops)

    session.commit()
    db_ops.close()

    response = {
        "message": "Image uploaded and sized",
        "image_id": new_image.id,
        "size_info": size_info
    }

    return jsonify(response), 200

@app.route("/images/", methods=["GET"])
def get_images_data():
    session = start()
    db_ops = DatabaseOperations(session)
    images = db_ops.session.query(Image).all()
    image_list = [
        {
            "id": image.id,
            "name": image.name,
            "image": image.base64_data,
            "flocs": [{"id": floc.id, "size": floc.size} for floc in image.flocs],
        }
        for image in images
    ]
    db_ops.close()
    return jsonify(image_list), 200

@app.route("/images/floc_sum", methods=["GET"])
def get_sum_of_floc_areas():
    n = request.args.get("limit", default=10, type=int)

    if n <= 0:
        return jsonify({"error": "Invalid limit value provided."}), 400

    session = start()
    db_ops = DatabaseOperations(session)
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()

    floc_sums = [
        db_ops.session.query(func.sum(Floc.size)).filter(Floc.image_id == image.id).scalar() or 0
        for image in images
    ]

    db_ops.close()
    return jsonify({"sum_floc_areas": floc_sums}), 200

@app.route("/images/floc_areas", methods=["GET"])
def get_floc_areas():
    n = request.args.get("limit", default=10, type=int)

    if n <= 0:
        return jsonify({"error": "Invalid limit value provided."}), 400

    session = start()
    db_ops = DatabaseOperations(session)
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()

    floc_areas = [
        [floc.size for floc in db_ops.session.query(Floc.size).filter(Floc.image_id == image.id).all()]
        for image in images
    ]

    db_ops.close()
    return jsonify({"floc_areas": floc_areas}), 200

@app.route("/images/floc_count", methods=["GET"])
def get_floc_count():
    n = request.args.get("limit", default=10, type=int)

    if n <= 0:
        return jsonify({"error": "Invalid limit value provided."}), 400

    session = start()
    db_ops = DatabaseOperations(session)
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()

    floc_counts = [
        db_ops.session.query(func.count(Floc.id)).filter(Floc.image_id == image.id).scalar() or 0
        for image in images
    ]

    db_ops.close()
    return jsonify({"floc_counts": floc_counts}), 200

@app.route("/images/latest", methods=["GET"])
def get_last_n_images():
    n = request.args.get("limit", default=10, type=int)

    if n <= 0:
        return jsonify({"error": "Invalid limit value provided."}), 400

    session = start()
    db_ops = DatabaseOperations(session)
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()

    image_list = [
        {
            "id": image.id,
            "name": image.name,
            "image": image.base64_data,
            "flocs": [{"id": floc.id, "size": floc.size} for floc in image.flocs],
        }
        for image in images
    ]

    db_ops.close()
    return jsonify(image_list), 200

if __name__ == "__main__":
    app.run(debug=True)
