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
    """
    Uploads an image to the database and sizes the image.
    """
    body = json.loads(request.data)
    image_base64_data = body.get("image")
    filePath = body.get("filePath")

    # Path to the filename.txt in the source directory
    filename_path = os.path.join(os.path.dirname(__file__), "filename.txt")

    if filePath:
        filePath = filePath
    elif os.path.exists(filename_path):
        with open(filename_path, "r") as file:
            filePath = file.read().strip()
    else:
        return jsonify({"error": "No file path provided and filename.txt does not exist."}), 400

    with open(filename_path, "w") as file:
        file.write(filePath)

    if filePath is None:
        return jsonify({"error": "No file path provided"}), 400

    session = start()
    db_ops = DatabaseOperations(session)
    current_id = db_ops.get_current_image_id()

    if current_id is None:
        image_name = "image0"
    else:
        image_name = f"image{current_id+1}"

    filePath = filePath + "/" + image_name + ".jpeg"
    if "," in image_base64_data:
        image_base64_data = image_base64_data.split(",")[1]
    image_data = base64.b64decode(image_base64_data)
    
    # Save the image to disk
    with open(filePath, "wb") as file:
        file.write(image_data)

    # Add image to the database
    new_image = db_ops.add_image(image_name, image_base64_data)

    # Size the image using the size script
    size_info = size.size_image(filePath, session, db_ops)

    # Commit the new image to the database
    session.commit()
    db_ops.close()

    response = {
        "message": "Image uploaded and sized",
        "image_id": new_image.id,
        "size_info": size_info  # Include the size information in the response
    }

    return jsonify(response), 200

@app.route("/images/", methods=["GET"])
def get_images_data():
    """
    Gets all image data in database
    """
    session = start()
    db_ops = DatabaseOperations(session)
    images = db_ops.session.query(Image).all()
    image_list = []
    for image in images:
        image_dict = {
            "id": image.id,
            "name": image.name,
            "image": image.base64_data,
            "flocs": [{"id": floc.id, "size": floc.size} for floc in image.flocs],
        }
        image_list.append(image_dict)

    db_ops.close()
    return jsonify(image_list), 200

@app.route("/images/<int:image_id>/data/", methods=["GET"])
def get_specific_image_data(image_id):
    """
    Gets the image data at for the specified image id
    """
    session = start()
    db_ops = DatabaseOperations(session)
    image = db_ops.session.query(Image).filter_by(id=image_id).first()

    if not image:
        return jsonify({"error": "Image not found"}), 404

    image_data = {
        "id": image.id,
        "name": image.name,
        "image": image.base64_data,
        "flocs": [{"id": floc.id, "size": floc.size} for floc in image.flocs],
    }

    db_ops.close()
    return jsonify(image_data), 200

@app.route("/images/<int:image_id>/", methods=["GET"])
def get_image(image_id):
    """
    Gets the image at the specified id
    """
    session = start()
    db_ops = DatabaseOperations(session)
    image = db_ops.session.query(Image).filter_by(id=image_id).first()

    if not image:
        return jsonify({"error": "Image not found"}), 404

    response = {"image": image.base64_data}
    db_ops.close()

    return jsonify(response), 200

@app.route("/images/floc_sum", methods=["GET"])
def get_sum_of_floc_areas():
    """
    Gets the sum of floc areas for each of the last n images
    """
    body = json.loads(request.data)
    n = body.get("limit")
    
    if not n or not isinstance(n, int) or n <= 0:
        return jsonify({"error": "Invalid limit value provided."}), 400

    session = start()
    db_ops = DatabaseOperations(session)

    # Query the last n images
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()
    if not images:
        db_ops.close()
        return jsonify({"error": "No images found."}), 404

    # Calculate the sum of floc areas for each of the last n images
    floc_sums = []
    for image in images:
        floc_sum = db_ops.session.query(func.sum(Floc.size)).filter(Floc.image_id == image.id).scalar()
        floc_sums.append(floc_sum if floc_sum else 0)

    db_ops.close()
    
    return jsonify({"sum_floc_areas": floc_sums}), 200

@app.route("/images/floc_areas", methods=["GET"])
def get_floc_areas():
    """
    Gets the floc areas for each of the last n images as an array of arrays
    """
    body = json.loads(request.data)
    n = body.get("limit")
    
    if not n or not isinstance(n, int) or n <= 0:
        return jsonify({"error": "Invalid limit value provided."}), 400

    session = start()
    db_ops = DatabaseOperations(session)

    # Query the last n images
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()
    if not images:
        db_ops.close()
        return jsonify({"error": "No images found."}), 404

    # Get the floc areas for each of the last n images
    floc_areas = []
    for image in images:
        flocs = db_ops.session.query(Floc.size).filter(Floc.image_id == image.id).all()
        floc_areas.append([floc.size for floc in flocs])

    db_ops.close()
    
    return jsonify({"floc_areas": floc_areas}), 200

@app.route("/images/floc_count", methods=["GET"])
def get_floc_count():
    """
    Gets the total number of flocs for each of the last n images
    """
    body = json.loads(request.data)
    n = body.get("limit")
    
    if not n or not isinstance(n, int) or n <= 0:
        return jsonify({"error": "Invalid limit value provided."}), 400

    session = start()
    db_ops = DatabaseOperations(session)

    # Query the last n images
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()
    if not images:
        db_ops.close()
        return jsonify({"error": "No images found."}), 404

    # Get the total number of flocs for each of the last n images
    floc_counts = []
    for image in images:
        floc_count = db_ops.session.query(func.count(Floc.id)).filter(Floc.image_id == image.id).scalar()
        floc_counts.append(floc_count if floc_count else 0)

    db_ops.close()
    
    return jsonify({"floc_counts": floc_counts}), 200

@app.route("/images/latest", methods=["GET"])
def get_last_n_images():
    """
    Gets the last n images
    """
    body = json.loads(request.data)
    n = body.get("limit")
    session = start()
    db_ops = DatabaseOperations(session)
    images = db_ops.session.query(Image).order_by(Image.id.desc()).limit(n).all()
    image_list = []
    for image in images:
        image_dict = {
            "id": image.id,
            "name": image.name,
            "image": image.base64_data,
            "flocs": [{"id": floc.id, "size": floc.size} for floc in image.flocs],
        }
        image_list.append(image_dict)
    db_ops.close()
    return jsonify(image_list), 200

@app.route("/images/<int:image_id>/", methods=["DELETE"])
def delete_image(image_id):
    """
    Deletes the image at the specified id
    """
    session = start()
    db_ops = DatabaseOperations(session)

    image = db_ops.session.query(Image).filter_by(id=image_id).first()

    if not image:
        return jsonify({"error": "Image not found"}), 404

    db_ops.session.delete(image)
    db_ops.session.commit()

    db_ops.close()
    return jsonify({"message": "Image deleted successfully"}), 200


@app.route("/images/", methods=["DELETE"])
def delete_all_images():
    """
    Deletes all images in the database
    """
    session = start()
    db_ops = DatabaseOperations(session)

    images = db_ops.session.query(Image).all()

    for image in images:
        db_ops.session.delete(image)
    db_ops.session.commit()

    db_ops.close()
    return jsonify({"message": "All images deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
