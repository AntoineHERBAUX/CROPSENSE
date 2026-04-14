from datetime import datetime, timedelta
from pymongo import MongoClient
import gridfs

def save_to_cropsense_db(db, fs, plant_id, timestamp, ms_data, thermal_data, hs_data):
    # 1. CREATE "ANCHOR" (CAPTURE EVENT)
    event_doc = {
        "sample_id": plant_id,
        "timestamp": timestamp,
        "capture_status": "complete",
        "ingested_at": datetime.utcnow()
    }
    
    # ✂️ La suite de votre fonction reste exactement la même !
    event_id = db['capture_events'].insert_one(event_doc).inserted_id

    # 2. SAVE MULTISPECTRAL
    if ms_data:
        ms_gridfs_id = fs.put(ms_data['raw_tiff'], filename=ms_data['filename'])
        ms_doc = {
            "capture_event_id": event_id,
            "gridfs_ref": ms_gridfs_id,
            "captured_at": ms_data['captured_at'],
            "integration_time_ms": ms_data['integration_time_ms'],
            "ndvi": ms_data['ndvi'],
            "histogram_256": ms_data['histogram']
        }
        db['sensors_multispectral'].insert_one(ms_doc)

    # 3. SAVE THERMAL
    if thermal_data:
        thermal_gridfs_id = fs.put(thermal_data['raw_file'], filename=thermal_data['filename'])
        thermal_doc = {
            "capture_event_id": event_id,
            "gridfs_ref": thermal_gridfs_id,
            "captured_at": thermal_data['captured_at'],
            "ambient_temp_c": thermal_data['ambient_temp'],
            "max_leaf_temp_c": thermal_data['max_leaf_temp'],
            "cwsi": thermal_data['cwsi']
        }
        db['sensors_thermal'].insert_one(thermal_doc)

    # 4. SAVE HYPERSPECTRAL 
    if hs_data:
        hs_gridfs_id = fs.put(hs_data['raw_cube'], filename=hs_data['filename'])
        hs_doc = {
            "capture_event_id": event_id,
            "gridfs_ref": hs_gridfs_id,
            "captured_at": hs_data['captured_at'],
            "spectral_range_nm": hs_data['spectral_range'],
            "mean_signature": hs_data['mean_signature']
        }
        db['sensors_hyperspectral'].insert_one(hs_doc)
        
    print(f"Data successfully inserted into collections for Event: {event_id}")


def get_mongo_client():
    """Attempts to connect to MongoDB using the provided list of URIs."""
    for uri in URIS_TO_TRY:
        print(f"Attempt to connect to MongoDB on {uri}")
        try:
            client = MongoClient(uri, 27017, serverSelectionTimeoutMS=2000)
            client.server_info() # Force connection check
            print(f"✅ Connected to MongoDB on {uri}")
            return client
        except:
            continue
    print("❌ Critical Error: No database accessible.")
    return None

    def find_thermal_cluster(spectral_path, plant_id, tolerance=300):
    """
    Finds the cluster of 4 Workswell thermal files corresponding to the spectral image timestamp, according to their ID.
    Searches in all 'Thermal' subfolders for the same date.
    """
    matches = {}
    spec_time = datetime.fromtimestamp(os.path.getmtime(spectral_path))
    
    # 1. Construct the specific target path
    # Structure: DATA / Date / PlantID / Spectral  --> We want DATA / Date / PlantID / Thermal
    spectral_folder = os.path.dirname(spectral_path)    # .../PlantID/Spectral
    plant_root = os.path.dirname(spectral_folder)       # .../PlantID
    target_thermal_dir = os.path.join(plant_root, "Thermal")
    
    # 2. Immediate exit if the folder doesn't exist for THIS plant
    if not os.path.exists(target_thermal_dir): 
        return matches

    # 3. Scan ONLY this specific directory
    for f in os.listdir(target_thermal_dir):
        f_path = os.path.join(target_thermal_dir, f)
        
        # Skip directories
        if os.path.isdir(f_path): continue
        
        # Check time
        therm_time = datetime.fromtimestamp(os.path.getmtime(f_path))
        
        if abs((spec_time - therm_time).total_seconds()) <= tolerance:
            if "visible" in f: matches["visual_rgb"] = f_path
            elif "radiometric" in f: matches["radiometric_jpg"] = f_path
            elif "thermo" in f: matches["raw_thermal_tiff"] = f_path
            elif "cwsi" in f: matches["cwsi_tiff"] = f_path
                    
    return matches


def save_gridfs_file(fs, file_id, folder, default_name):
    """Helper function to save a single file from GridFS"""
    try:
        grid_out = fs.get(file_id)
        
        # Use the real filename if available in GridFS metadata
        if grid_out.filename:
            final_name = grid_out.filename
        else:
            final_name = default_name
            
        output_path = os.path.join(folder, final_name)
        
        # Skip if already exists
        if os.path.exists(output_path):
            return

        with open(output_path, 'wb') as f:
            f.write(grid_out.read())
            
    except Exception as e:
        print(f"      -> Failed to save file {file_id}: {e}")

def process_independent_thermal(date_folder_path, db_collection, fs):
    """
    Scans for thermal files that were NOT linked to a spectral event and uploads them.
    No specific tag is added to the database; the spectral field will simply be Null.
    
    Args:
        date_folder_path (str): Path to the Date folder (e.g., .../2025-12-10/)
        db_collection: MongoDB collection object
        fs: GridFS object
    """
    print(f"\n🔄 [Independent Thermal] Scanning for standalone thermal data in {os.path.basename(date_folder_path)}...")
    
    count_new = 0
    
    # 1. Walk through all folders in this Date
    for root, dirs, files in os.walk(date_folder_path):
        folder_name = os.path.basename(root)
        
        # We only care about "Thermal" folders
        if folder_name != "Thermal":
            continue
            
        # Deduce Plant ID from parent folder (e.g. .../P01/Thermal -> P01)
        plant_id = os.path.basename(os.path.dirname(root))
        
        # 2. Group files by 'Shot' (Timestamp prefix)
        # Workswell files look like: "14-20-00-123-thermo.tiff"
        shots = {}
        
        for f in files:
            # Simple regex to capture the HH-MM-SS-mmm prefix
            match = re.match(r"^(\d{2}-\d{2}-\d{2}-\d{3})", f)
            if match:
                prefix = match.group(1)
                if prefix not in shots: shots[prefix] = {}
                
                full_path = os.path.join(root, f)
                
                # Assign type
                if "visible" in f: shots[prefix]["visual_rgb"] = full_path
                elif "radiometric" in f: shots[prefix]["radiometric_jpg"] = full_path
                elif "thermo" in f: shots[prefix]["raw_thermal_tiff"] = full_path
                elif "cwsi" in f: shots[prefix]["cwsi_tiff"] = full_path

        # 3. Process each shot
        for prefix, file_dict in shots.items():
            
            # CHECK: Does this thermal data already exist in DB?
            # We look for the filename in the 'sensor_thermal' section to avoid duplicates.
            if "raw_thermal_tiff" in file_dict:
                ref_filename = os.path.basename(file_dict["raw_thermal_tiff"])
                exists = db_collection.find_one({"sensor_thermal.original_filename": ref_filename})
                
                if exists:
                    # Already processed (either via Spectral Fusion or previously imported) -> Skip
                    continue
            
            # 4. If not in DB, it's a new Independent Event
            stored_files_ids = {}
            
            # Upload files to GridFS
            for f_type, f_path in file_dict.items():
                try:
                    with open(f_path, 'rb') as f_in:
                        # We upload to GridFS
                        fid = fs.put(f_in, filename=os.path.basename(f_path), content_type="image/tiff")
                        stored_files_ids[f_type] = fid
                except Exception as e:
                    print(f"   ⚠️ Error uploading {f_path}: {e}")

            # Create Database Document
            try:
                # Reconstruct timestamp from filename (HH-MM-SS-mmm) and Folder Date
                time_parts = prefix.split("-") # ['14', '20', '00', '123']
                date_str = os.path.basename(date_folder_path) # '2025-12-10'
                
                # Format: YYYY-MM-DD HH:MM:SS
                timestamp_str = f"{date_str} {time_parts[0]}:{time_parts[1]}:{time_parts[2]}"
                
                event_doc = {
                    "context": {
                        "plant_id": plant_id,
                        "timestamp": timestamp_str
                        # No 'mode' tag added here, keeping it clean.
                    },
                    "sensor_multispectral": None, # Explicitly Empty
                    "sensor_thermal": {
                        "camera_model": "WORKSWELL WIRIS AGRO R",
                        "original_filename": os.path.basename(file_dict.get("raw_thermal_tiff", "unknown")),
                        "files": stored_files_ids,
                        "detected_count": len(stored_files_ids)
                    }
                }
                
                db_collection.insert_one(event_doc)
                print(f"   ✅ Saved Thermal Event (No Spectral): {plant_id} @ {time_parts[0]}:{time_parts[1]}")
                count_new += 1
                
            except Exception as e:
                print(f"   ❌ Error saving doc: {e}")

    print(f"   -> Added {count_new} new independent thermal events.")

def export_file_from_db(output_folder, plant_id=None, sensor_type='spectral', thermal_file_type='radiometric_jpg', mongo_uri='localhost', db_name='cropsense_db'):
    """
    Retrieves a file (Spectral OR Thermal) from MongoDB and saves it to disk.
    
    Parameters:
    - output_folder (str): Destination folder.
    - plant_id (str, optional): ID of the plant (e.g., "P01"). If None, takes the latest event.
    - sensor_type (str): 'spectral' OR 'thermal'.
    - thermal_file_type (str): Only if sensor_type='thermal'. 
                               Options: 'visual_rgb', 'radiometric_jpg', 'raw_thermal_tiff', 'cwsi_tiff'.
    """
    
    # 1. Connect to DB
    try:
        client = MongoClient(mongo_uri, 27017, serverSelectionTimeoutMS=2000)
        db = client[db_name]
        fs = gridfs.GridFS(db)
        coll = db['capture_events']
        client.server_info()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

    # 2. Find Event
    query = {}
    if plant_id:
        query["context.plant_id"] = plant_id
        print(f"🔍 Searching last event for plant: {plant_id}...")
    else:
        print("🔍 Searching for the very last event recorded...")

    event = coll.find_one(query, sort=[("context.timestamp", -1)])
    if not event:
        print("⚠️ No event found.")
        return None

    # 3. Identify File ID based on request
    file_id = None
    original_filename = "unknown_file"

    try:
        if sensor_type == 'spectral':
            # Get the main TIFF file
            data_node = event.get('sensor_multispectral', {})
            file_id = data_node.get('raw_file_id')
            original_filename = data_node.get('filename', 'spectral.tif')
            
        elif sensor_type == 'thermal':
            # Get one of the 4 thermal files
            files_node = event.get('sensor_thermal', {}).get('files', {})
            
            # Map the user request to the database keys.
            # Keys are stored as plain names (e.g. "radiometric_jpg"), NOT with _id suffix.
            db_key = thermal_file_type  # e.g. "radiometric_jpg"
            
            file_id = files_node.get(db_key)
            
            # We try to reconstruct a name (since it wasn't explicitly stored in the simplified node)
            # But GridFS knows the name! We will get it later.
            original_filename = f"thermal_{thermal_file_type}.img" 

        # 4. Download and Save
        if not file_id:
            print(f"⚠️ No file found for sensor '{sensor_type}' (Type: {thermal_file_type}) in this event.")
            return None

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Retrieve from GridFS
        grid_out = fs.get(file_id)
        data = grid_out.read()
        
        # Use the real filename stored in GridFS if possible
        if grid_out.filename:
            original_filename = grid_out.filename
            
        output_path = os.path.join(output_folder, original_filename)
        
        with open(output_path, 'wb') as f:
            f.write(data)
            
        print(f"✅ File saved: {output_path}")
        print(f"   (Source: {sensor_type} | Date: {event['context']['timestamp']})")
        return output_path

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return None

def batch_export_all():
    print(f"🚀 Starting Batch Export to: {EXPORT_ROOT}")
    
    # 1. Connection
    try:
        client = MongoClient(MONGO_URI, 27017, serverSelectionTimeoutMS=2000)
        db = client[DB_NAME]
        fs = gridfs.GridFS(db)
        coll = db['capture_events']
        client.server_info()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Get ALL events
    # You can add a filter here, e.g., {"context.plant_id": "P01"}
    cursor = coll.find({}) 
    total_docs = coll.count_documents({})
    
    print(f"📦 Found {total_docs} events to process...")

    count = 0
    for doc in cursor:
        try:
            # 3. Context Info
            context = doc.get('context', {})
            plant_id = context.get('plant_id', 'Unknown')
            # Safe timestamp handling
            ts = context.get('timestamp')
            if isinstance(ts, str): # If stored as string
                date_str = ts[:10] # YYYY-MM-DD
            elif isinstance(ts, datetime): # If stored as Date object
                date_str = ts.strftime('%Y-%m-%d')
            else:
                date_str = "NoDate"

            # 4. Create Target Folder
            # Structure: EXPORT / PlantID / Date
            target_folder = os.path.join(EXPORT_ROOT, plant_id, date_str)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            # 5. Export Spectral File
            spec_node = doc.get('sensor_multispectral', {})
            spec_id = spec_node.get('raw_file_id')
            if spec_id:
                filename = spec_node.get('filename', f"spectral_{plant_id}.tif")
                save_gridfs_file(fs, spec_id, target_folder, filename)

            # 6. Export Thermal Files
            therm_node = doc.get('sensor_thermal', {}).get('files', {})
            for file_type, file_id in therm_node.items():
                # file_type is like "radiometric_jpg_id"
                # We construct a name if the original isn't stored, or get it from GridFS
                filename = f"thermal_{file_type}.img" 
                save_gridfs_file(fs, file_id, target_folder, filename)

            count += 1
            print(f"   [{count}/{total_docs}] Processed {plant_id} ({date_str})")

        except Exception as e:
            print(f"   ❌ Error processing doc {doc.get('_id')}: {e}")

    print("\n✅ Batch Export Completed.")

def sanitize_for_mongo(data):
    if isinstance(data, dict):
        return {k: sanitize_for_mongo(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_mongo(v) for v in data]
    elif isinstance(data, np.ndarray):
        if data.size > 1000:
            return f"Excluded ndarray of shape {data.shape} to save space"
        return data.tolist()
    elif isinstance(data, np.generic): 
        return data.item()
    return data



def get_or_create_capture_event(db, sample_id, timestamp):
    """
    Implements the 10-Minute Synchronization Window logic.
    Finds an existing event within +/- 10 mins, or creates a new one.
    """
    events_coll = db["capture_events"]
    
    # 10-minute window window boundary
    start_time = timestamp - timedelta(minutes=10)
    end_time = timestamp + timedelta(minutes=10)
    
    # Check if an event already exists for this plant in that timeframe
    existing_event = events_coll.find_one({
        "sample_id": sample_id,
        "timestamp": {"$gte": start_time, "$lte": end_time}
    })
    
    if existing_event:
        return existing_event["_id"]
    
    # If not, create a new central hub event
    new_event = {
        "sample_id": sample_id,
        "timestamp": timestamp,
        "capture_status": "complete", 
        "ingested_at": datetime.utcnow()
    }
    result = events_coll.insert_one(new_event)
    return result.inserted_id


def export_recent_files(output_folder, limit=5, plant_id=None, sensor_type='spectral', thermal_file_type='radiometric_jpg', mongo_uri='localhost', db_name='cropsense_db'):
    """
    Retrieves the last 'n' images recorded in the database.
    
    Parameters:
    - output_folder (str): Folder where files will be saved.
    - limit (int): Number of files to retrieve (default 5).
    - plant_id (str, optional): Filter by plant (e.g., "P01"). If None, takes all plants.
    - sensor_type (str): 'spectral' OR 'thermal'.
    - thermal_file_type (str): If thermal, which file? ('visual_rgb', 'radiometric_jpg', etc.)
    """
    
    # 1. Connection
    try:
        client = MongoClient(mongo_uri, 27017, serverSelectionTimeoutMS=2000)
        db = client[db_name]
        fs = gridfs.GridFS(db)
        coll = db['capture_events']
        client.server_info()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Query Configuration
    query = {}
    if plant_id:
        query["context.plant_id"] = plant_id
        print(f"🔍 Searching for the last {limit} images for plant: {plant_id}...")
    else:
        print(f"🔍 Searching for the last {limit} images (all plants)...")

    # 3. Retrieve cursor (Sorted by date DESC)
    # .limit(limit) restricts the number of results
    cursor = coll.find(query).sort("context.timestamp", -1).limit(limit)
    
    count = 0
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 4. Loop through results
    for event in cursor:
        try:
            # -- Same logic as the single function to find the ID --
            file_id = None
            filename_prefix = ""

            if sensor_type == 'spectral':
                data_node = event.get('sensor_multispectral', {})
                file_id = data_node.get('raw_file_id')
                # We add the timestamp to the name to avoid duplicates if filenames are identical
                ts_str = event['context']['timestamp'].strftime("%H%M%S")
                original_name = data_node.get('filename', 'spec.tif')
                
            elif sensor_type == 'thermal':
                files_node = event.get('sensor_thermal', {}).get('files', {})
                db_key = f"{thermal_file_type}_id"
                file_id = files_node.get(db_key)
                ts_str = event['context']['timestamp'].strftime("%H%M%S")
                original_name = f"thermal_{thermal_file_type}.img"

            # -- Download --
            if file_id:
                grid_out = fs.get(file_id)
                # If GridFS has the real name, use it, otherwise use the constructed one
                final_name = grid_out.filename if grid_out.filename else original_name
                
                # Security: To avoid overwriting, we can prefix with the plant ID
                p_id = event['context']['plant_id']
                save_name = f"{p_id}_{final_name}"
                
                output_path = os.path.join(output_folder, save_name)
                
                with open(output_path, 'wb') as f:
                    f.write(grid_out.read())
                
                print(f"   ✅ [{count+1}/{limit}] Saved: {save_name}")
                count += 1
            else:
                print(f"   ⚠️ Event found but no file for this sensor (Plant: {event['context']['plant_id']})")

        except Exception as e:
            print(f"   ❌ Error on a file: {e}")

    print(f"🚀 Completed. {count} files exported to {output_folder}")

def check_database_integrity(plant_id_to_check, mongo_uri='localhost', db_name='cropsense_db'):
    """
    Diagnose function to verify if files for a specific plant are correctly stored in GridFS.
    
    Args:
        plant_id_to_check (str): The Plant ID to look for (e.g., "FirstTests", "PO1").
        mongo_uri (str): Address of the MongoDB server.
    """
    print(f"\n🔍 --- DIAGNOSIS FOR PLANT: {plant_id_to_check} ---")
    
    # 1. Connection
    try:
        client = MongoClient(mongo_uri, 27017, serverSelectionTimeoutMS=2000)
        db = client[db_name]
        fs = gridfs.GridFS(db)
        coll = db['capture_events']
        client.server_info() # Check connection
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 2. General Stats
    total_files = db['fs.files'].count_documents({})
    print(f"📦 Total binary files in GridFS (All plants): {total_files}")

    # 3. Find the Document
    # We look for the most recent event for this plant
    event = coll.find_one({"context.plant_id": plant_id_to_check}, sort=[("context.timestamp", -1)])

    if not event:
        print(f"❌ No metadata document found for plant '{plant_id_to_check}'.")
        print("   -> Check if the Plant ID is correct (Case sensitive!).")
        return

    print(f"✅ Metadata document found (Date: {event['context']['timestamp']})")

    # 4. Check Spectral File
    print("\n   [Spectral Sensor]")
    spec_id = event.get('sensor_multispectral', {}).get('raw_file_id')
    if spec_id:
        if fs.exists(spec_id):
            file_meta = fs.get(spec_id)
            print(f"     ✅ RAW TIFF exists (Size: {file_meta.length / 1024 / 1024:.2f} MB)")
        else:
            print(f"     ❌ ERROR: File ID exists in document but file is missing in GridFS!")
    else:
        print("     ⚠️ No Spectral file linked.")

    # 5. Check Thermal Files
    print("\n   [Thermal Sensor]")
    thermal_files = event.get('sensor_thermal', {}).get('files', {})
    
    if not thermal_files:
        print("     ⚠️ No Thermal files linked (Empty list).")
    else:
        for file_type, file_id in thermal_files.items():
            if fs.exists(file_id):
                file_meta = fs.get(file_id)
                print(f"     ✅ {file_type}: OK (Size: {file_meta.length / 1024:.2f} KB)")
            else:
                print(f"     ❌ {file_type}: Missing body in GridFS (ID: {file_id})")