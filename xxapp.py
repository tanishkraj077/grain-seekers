from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

client = MongoClient('mongodb://localhost:27017/')
db = client['sih']

@app.route("/api/beaches")
def get_beaches():
    try:
        logger.info("Fetching beaches list from database")
        beaches_collection = db['1beaches']
        beaches = list(beaches_collection.find({}, {"_id": 1, "name": 1, "lat": 1, "lon": 1}))
        
        logger.info(f"Found {len(beaches)} beaches")
        for beach in beaches:
            beach["_id"] = str(beach["_id"])
            logger.debug(f"Beach: {beach['name']} (ID: {beach['_id']})")
            
        return jsonify(beaches)
    except Exception as e:
        logger.error(f"Error fetching beaches: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/runs/<beach_id>")
def get_runs(beach_id):
    try:
        logger.info(f"Fetching runs for beach ID: {beach_id}")
        collection_names = db.list_collection_names()
        logger.debug(f"Available collections: {collection_names}")
        
        object_id = None
        try:
            object_id = ObjectId(beach_id)
            logger.debug(f"Converted beach_id to ObjectId: {object_id}")
        except:
            object_id = beach_id
            logger.debug(f"Using beach_id as string: {beach_id}")
            
        beach_collection_name = None
        for name in collection_names:
            if name == beach_id or name == str(object_id):
                beach_collection_name = name
                break
                
        if not beach_collection_name:
            logger.warning(f"Beach collection not found for ID: {beach_id}")
            return jsonify({"error": f"Beach '{beach_id}' not found."}), 404
            
        logger.info(f"Found beach collection: {beach_collection_name}")
        beach_doc = db[beach_collection_name].find_one({})
        
        if beach_doc:
            logger.info(f"Retrieved beach document with {len(beach_doc.get('runs', []))} runs")
            
            # Log detailed structure information
            if "runs" in beach_doc:
                logger.info(f"Total runs: {len(beach_doc['runs'])}")
                for i, run in enumerate(beach_doc["runs"]):
                    locations_count = len(run.get("locations", []))
                    total_grains = sum(len(loc.get("grains", [])) for loc in run.get("locations", []))
                    logger.info(f"Run {i+1}: {run.get('operation_id', 'N/A')} - {locations_count} locations, {total_grains} total grains")
                    
                    # Log sample grain data for first location of first run
                    if i == 0 and run.get("locations"):
                        first_loc = run["locations"][0]
                        grains = first_loc.get("grains", [])
                        if grains:
                            logger.debug(f"Sample grain data - First location, first run:")
                            logger.debug(f"  Grains count: {len(grains)}")
                            logger.debug(f"  First grain: diameter={grains[0].get('diameter', 'N/A')}, area={grains[0].get('area', 'N/A')}")
            
            if "_id" in beach_doc and isinstance(beach_doc["_id"], ObjectId):
                beach_doc["_id"] = str(beach_doc["_id"])
            
            if "name" not in beach_doc:
                beach_info_id = object_id if isinstance(object_id, ObjectId) else ObjectId(beach_id) if len(beach_id) == 24 else beach_id
                beach_info = db['1beaches'].find_one({"_id": beach_info_id})
                beach_doc["name"] = beach_info["name"] if beach_info and "name" in beach_info else "Unknown Beach"
                logger.info(f"Retrieved beach name from 1beaches: {beach_doc['name']}")
            
            if "runs" not in beach_doc:
                beach_doc["runs"] = []
                logger.warning("No runs found in beach document")
            
            for run in beach_doc["runs"]:
                run.setdefault("operation_id", f"run_{run.get('date', 'unknown')}")
                run.setdefault("locations", [])
                for location in run["locations"]:
                    location.setdefault("grains", [])
            
            logger.info(f"Successfully processed beach data for: {beach_doc.get('name', 'Unknown')}")
            return jsonify(beach_doc)
        else:
            logger.error(f"Beach data not found in collection: {beach_collection_name}")
            return jsonify({"error": "Beach data not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching runs for beach {beach_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/health")
def health_check():
    logger.info("Health check requested")
    return jsonify({"status": "ok", "message": "Server is running"})

if __name__ == '__main__':
    logger.info("Starting Flask server on port 5000")
    app.run(debug=True, port=5000, threaded=True)