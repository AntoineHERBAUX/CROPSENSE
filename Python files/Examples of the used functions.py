#      _____                       _            _ _            
#     |  __ \                     (_)          | (_)           
#     | |__) |   _ _ __      _ __  _ _ __   ___| |_ _ __   ___ 
#     |  _  / | | | '_ \    | '_ \| | '_ \ / _ \ | | '_ \ / _ \
#     | | \ \ |_| | | | |   | |_) | | |_) |  __/ | | | | |  __/
#     |_|  \_\__,_|_| |_|   | .__/|_| .__/ \___|_|_|_| |_|\___|
#                     ______| |     | |                        
#                    |______|_|     |_|                        



#To classify everything, order in local, then sending it on the database
# ⚠️ RUN IT ONLY WHEN YOUR DATA IS CLEAN ⚠️

run_pipeline()



#     __      __        _                     __                  _   _                 
#     \ \    / /       (_)                   / _|                | | (_)                
#      \ \  / /_ _ _ __ _  ___  _   _ ___   | |_ _   _ _ __   ___| |_ _  ___  _ __  ___ 
#       \ \/ / _` | '__| |/ _ \| | | / __|  |  _| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
#        \  / (_| | |  | | (_) | |_| \__ \  | | | |_| | | | | (__| |_| | (_) | | | \__ \
#         \/ \__,_|_|  |_|\___/ \__,_|___/  |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
#                                                                                       
#                                                                                       

# To get the Spectral Image

export_file_from_db("./EXPORTS", plant_id="P01", sensor_type="spectral")


# To get the Thermal Radiometric Image (for reports)

export_file_from_db("./EXPORTS", plant_id="P01", sensor_type="thermal", thermal_file_type="radiometric_jpg")


# To get the Raw Thermal Data (for analysis):

export_file_from_db("./EXPORTS", plant_id="P01", sensor_type="thermal", thermal_file_type="raw_thermal_tiff")

# To clean everything on the database
# ⚠️ IT WILL DELETE EVERYTHING ON MONGODB⚠️

client = MongoClient('localhost', 27017)
client['cropsense_db']['capture_events'].drop()
print("Base de données nettoyée !")

#To export all the data from the database to your pc
batch_export_all()

# To rename your files from a prefix to an other prefix
rename_batch_prefix(PATH_INBOX, "Spectral_TestBatch_001_DARKREF_001", "Spectral_TestBatch_DARKREF_001")

# --- EXAMPLE: Export data to a CSV file ---
# This will create a file named 'Analysis_P01.csv' in your current folder.
# You can then open this file in Excel to make your own custom graphs.
df = export_analysis_to_csv("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff", output_csv="Analysis_P01_histogram.csv", analysis_type="histogram")


df = export_analysis_to_csv("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff", output_csv="Analysis_P01_profile.csv", analysis_type="profile")
# Optional: Print the first few rows to verify
print(df.head())



#      __  __       _ _   _                     _             _       __                  _   _                 
#     |  \/  |     | | | (_)                   | |           | |     / _|                | | (_)                
#     | \  / |_   _| | |_ _ ___ _ __   ___  ___| |_ _ __ __ _| |    | |_ _   _ _ __   ___| |_ _  ___  _ __  ___ 
#     | |\/| | | | | | __| / __| '_ \ / _ \/ __| __| '__/ _` | |    |  _| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
#     | |  | | |_| | | |_| \__ \ |_) |  __/ (__| |_| | | (_| | |    | | | |_| | | | | (__| |_| | (_) | | | \__ \
#     |_|  |_|\__,_|_|\__|_|___/ .__/ \___|\___|\__|_|  \__,_|_|    |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
#                              | |                                                                              
#                              |_|                                                                              


# Example 1: Show band by Index (0 = 410nm)
show_spectral_channel("C:/CROPSENSE/CROPSENSE_DATA/2026-03-18/rust/Spectral/Spectral_rust_4.tif", channel_index=5)
show_spectral_channel("C:/CROPSENSE/CROPSENSE_DATA/2026-03-18/rust/Spectral/Spectral_rust_4.tif", wavelength=740)

# Example 2: Show band by Wavelength (e.g., Red Edge 756nm)
show_spectral_channel("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff", wavelength=557)
show_spectral_image("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff")
show_spectral_image("C:/CROPSENSE/CROPSENSE_DATA/2026-03-18/rust/Spectral/Spectral_rust_4.tif")


# --- EXAMPLE 1: Check the "Red Edge" band (Index 7) of a multispectral file ---
# This helps you see if the specific band used for NDVI is well exposed.
spectral_file = "C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff"
plot_image_histogram(spectral_file, band_index=7, bins=100, log_scale=True)

#Spectral profile
plot_spectral_profile("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff", smooth=False)


# --- EXAMPLE 1: Overlay Mode (Recommended) ---
# Draws 10 colored lines. Perfect to see if ONE specific band is dead or saturated.
plot_full_spectral_histogram("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff", mode='overlay', log_scale=True)

# --- EXAMPLE 2: Global Mode ---
# Aggregates everything. Good to see the overall brightness of the image.
plot_full_spectral_histogram("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/test/Spectral/test_20251201_153000_830_00000000_raw.tiff", mode='global', log_scale=True)



#      _______ _                               _       __                  _   _                 
#     |__   __| |                             | |     / _|                | | (_)                
#        | |  | |__   ___ _ __ _ __ ___   __ _| |    | |_ _   _ _ __   ___| |_ _  ___  _ __  ___ 
#        | |  | '_ \ / _ \ '__| '_ ` _ \ / _` | |    |  _| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
#        | |  | | | |  __/ |  | | | | | | (_| | |    | | | |_| | | | | (__| |_| | (_) | | | \__ \
#        |_|  |_| |_|\___|_|  |_| |_| |_|\__,_|_|    |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
#                                                                                                
#                                                                                                

# --- EXAMPLE: Plot a thermic image file ---
# This will show the temperature and the water stress.
show_thermal_image("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/PreSample/Thermal/Thermal_PreSample_00-08-09-074-thermo.tiff")
show_thermal_image("C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/PreSample/Thermal/Thermal_PreSample_00-08-09-074-cwsi.tiff")


# --- EXAMPLE 2: Check a Thermal Temperature Map ---
# This shows the distribution of temperatures (e.g., most pixels are around 22°C).
thermal_file = "C:/CROPSENSE/CROPSENSE_DATA/2025-12-10/PreSample/Thermal/Thermal_PreSample_00-08-09-074-thermo.tiff"
plot_image_histogram(thermal_file, bins=50, log_scale=True)


#      _    _                                           _             _       __                  _   _                 
#     | |  | |                                         | |           | |     / _|                | | (_)                
#     | |__| |_   _ _ __   ___ _ __ ___ _ __   ___  ___| |_ _ __ __ _| |    | |_ _   _ _ __   ___| |_ _  ___  _ __  ___ 
#     |  __  | | | | '_ \ / _ \ '__/ __| '_ \ / _ \/ __| __| '__/ _` | |    |  _| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
#     | |  | | |_| | |_) |  __/ |  \__ \ |_) |  __/ (__| |_| | | (_| | |    | | | |_| | | | | (__| |_| | (_) | | | \__ \
#     |_|  |_|\__, | .__/ \___|_|  |___/ .__/ \___|\___|\__|_|  \__,_|_|    |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
#              __/ | |                 | |                                                                              
#             |___/|_|                 |_|                                                                              


#first we need to prepare the data 
hyperspectral_data = prepare_hyperspectral_data("C:/CROPSENSE/CROPSENSE_DATA/2026-04-09/TestBatch/Spectral/Spectral_TestBatch_001.hdr", "C:/CROPSENSE/CROPSENSE_DATA/2026-04-09/TestBatch/Spectral/Spectral_TestBatch_DARKREF_001.hdr", "C:/CROPSENSE/CROPSENSE_DATA/2026-04-09/TestBatch/Spectral/Spectral_TestBatch_WHITEREF_001.hdr", 'purple', 0.07, 0.72, 0.01)
#we can separate things if we have to
sick_plant, healthy_plant = separate_data(hyperspectral_data, ligne_coupe=800)



show_hyperspectral_image(hyperspectral_data)
show_hyperspectral_image(healthy_plant)
show_hyperspectral_image(sick_plant)
show_hyperspectral_graph(healthy_plant)
show_hyperspectral_graph(sick_plant)
show_multiple_hyperspectral_graphs([healthy_plant, sick_plant], ["Control Plant", "Inoculated Plant"])
ndvi_rayhana = calculate_mean_ndvi(hyperspectral_data, cible_nir=800, cible_red=670)
print(f"🌱 NVDI Formule Rayhana : {ndvi_rayhana:.5f}")
ndvi_yu = calculate_mean_ndvi(hyperspectral_data, cible_nir=800, cible_red=680)
print(f"🌱 NVDI Formule Yu : {ndvi_yu:.5f}")
print(f"🌱 GNVDI : {calculate_mean_gndvi(hyperspectral_data):.5f}")
print(f"🌱 RVI : {calculate_mean_rvi(hyperspectral_data):.5f}")
print(f"🌱 WI : {calculate_mean_wi(hyperspectral_data):.5f}")
print(f"🌱 NDWI : {calculate_mean_ndwi(hyperspectral_data):.5f}")
print(f"🌱 SIPI : {calculate_mean_sipi(hyperspectral_data):.5f}")
print(f"🌱 PRI : {calculate_mean_pri(hyperspectral_data):.5f}")
print(f"🌱 ARI : {calculate_mean_ari(hyperspectral_data):.5f}")
print(f"🌱 CARI : {calculate_mean_cari(hyperspectral_data):.5f}")


tableau_comparative = compare_plants_indices([healthy_plant, sick_plant], ["Control Plant", "Inoculated Plant"])



#explain_spectral_index("PRI")
explain_spectral_index("ALL")

# Show the table
tableau_comparative