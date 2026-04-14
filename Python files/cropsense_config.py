

PATH_INBOX = "C:/CROPSENSE/INBOX"          # Inbox folder (Camera software output)
PATH_DATA_ROOT = "C:/CROPSENSE/CROPSENSE_DATA" # Hierarchical final storage
PATH_EXPORT = "C:/CROPSENSE/EXPORTED_FROM_DB" # Path where exported data from database will be stored
CSV_LOG_PATH = "./experience_log.csv"      # Ground Truth tracking file

# MongoDB Connection (Auto-switch Local/Server)
URIS_TO_TRY = ['172.20.10.8', 'localhost'] # Add your server IPs here
DB_NAME = 'cropsense_db'
COLLECTION_NAME = 'capture_events'

# Define SILIOS Wavelengths mapping for easier access
SILIOS_WAVELENGTHS = {
    0: "410nm", 1: "463nm", 2: "500nm", 3: "557nm", 4: "605nm",
    5: "666nm", 6: "693nm", 7: "756nm", 8: "807nm", 9: "869nm"
}


# SILIOS TOUCAN Demosaicing Matrix (Fixed Pattern)
# Source: TOUCAN Matrix Filter arrangement V1.0
TOUCAN_PATTERN = {
    0: [(0,3), (2,1)], 1: [(0,1), (2,3)], 2: [(2,0)], 3: [(0,0), (2,2)],
    4: [(1,2)], 5: [(3,0)], 6: [(1,0)], 7: [(1,3), (3,1)],
    8: [(1,1), (3,3)], 9: [(3,2)]
}