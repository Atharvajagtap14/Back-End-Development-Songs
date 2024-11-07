from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"})

@app.route("/count", methods=["GET"])
def count():
    # Count the documents in the songs collection
    song_count = db.songs.count_documents({})
    return jsonify({"count": song_count})

@app.route("/song", methods=["GET"])
def songs():
    # Query to find all documents in the songs collection
    songs_data = list(db.songs.find({}))
    # Parse the data to JSON format and return it
    return jsonify({"songs": parse_json(songs_data)}), 200

@app.route("/song/<id>", methods=["GET"])
def get_song_by_id(id):
    try:
        # Query to find a document by id in the songs collection
        song_data = db.songs.find_one({"id": id})
        if not song_data:
            return jsonify({"message": "song with id not found"}), 404
        # Parse the song data to JSON format
        return jsonify(parse_json(song_data)), 200
    except Exception as e:
        return jsonify({"message": "Invalid song ID format"}), 400

@app.route("/song", methods=["POST"])
def create_song():
    # Extract song data from the request body
    song_data = request.get_json()
    
    # Check if "id" is provided in the song data
    if "id" not in song_data:
        return jsonify({"message": "Missing 'id' in request data"}), 400
    
    # Use the 'id' field in the song data
    song_id = song_data["id"]

    # Check if a song with this id already exists in the collection
    if db.songs.find_one({"id": song_id}):
        # If found, return a 302 status indicating duplicate
        return jsonify({"message": f"Song with id {song_id} already present"}), 302

    # If not found, insert the new song
    db.songs.insert_one(song_data)
    return jsonify({"message": "Song created successfully"}), 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    # Extract song data from the request body
    song_data = request.get_json()

    # Find the song in the database by id
    existing_song = db.songs.find_one({"id": id})

    if not existing_song:
        # If the song doesn't exist, return 404 with a message
        return jsonify({"message": "song not found"}), 404

    # Update the song with the new data
    db.songs.update_one({"id": id}, {"$set": song_data})

    # Return a success message with HTTP status 200 OK
    return jsonify({"message": "Song updated successfully"}), 200

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    # Use the db.songs.delete_one method to delete the song by id
    result = db.songs.delete_one({"id": id})

    # Check if the song was deleted (i.e., deleted_count > 0)
    if result.deleted_count == 0:
        # If no song was found with that id, return a 404 with a message
        return jsonify({"message": "song not found"}), 404

    # If the song was deleted successfully, return a 204 No Content status
    return '', 204

