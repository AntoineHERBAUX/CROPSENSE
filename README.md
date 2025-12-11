# CROPSENSE Data Processing Platform (V1)

## 📌 Project Overview
  Version: 1.0
  
  Context: CROPSENSE Project - Phase 1
  
  Objective: Early detection of plant leaf diseases using multispectral and thermal imaging.This repository contains the automated ETL (Extract, Transform, Load) pipeline designed to ingest, process, and store high-throughput phenotyping data. It bridges the gap between raw camera output (SILIOS & Workswell) and a structured MongoDB database, preparing the data for subsequent AI analysis.
  
  ## 🛠️ Prerequisites & Setup
  Before running the pipeline, ensure your environment is correctly configured.
  
  ### 1. Hardware Requirements
  #### Computer: 
  Windows Laptop/PC (Project Laptop).
  
  #### Cameras : 
  Multispectral: SILIOS CMS4/TOUCAN (USB).
  
  Thermal: Workswell WIRIS Agro R (USB/SD Card).
  
  #### Network: 
  Access to the local server (if applicable. Note : Junia Firewall blocks utilisation of MongoDB between differents PC/Servers.) or `localhost`.
  
  ### 2. Software Installation
  You need Python 3.10+ and a MongoDB server running.
  
  #### Install Python Libraries:
  Open your terminal (Command Prompt) and run: `pip install numpy pandas pymongo matplotlib opencv-python tifffile imagecodecs --user`

  #### Setup MongoDB: 
Install MongoDB Community Server.

Install MongoDB Compass (for visualization).

Ensure the MongoDB service is running (Task Manager > Services).

### 3. Folder Structure
Create the following folders on your C: drive (or configure paths in the script):

#### C:/CROPSENSE/INBOX 
*The "Drop Zone". Configure your camera software (Color Shades) to save images here*.

#### C:/CROPSENSE/CROPSENSE_DATA 
*The "Safe Storage". The script will automatically organize processed files here.*

## 📁 File Naming & Classification Rules

The pipeline uses a Priority Logic to classify files. It first looks for an Explicit Prefix (recommended for perfect sorting). If none is found, it falls back to Pattern Recognition to guess the file type and owner. Tip : Try to keep the same logic on naming sample.

### 1. Explicit Naming (Recommended)
Priority: High 

Use this format to force the pipeline to sort files exactly where you want them.

- Format: [SensorType] _ [PlantID] _ [FreeText].ext
- Keywords for [SensorType]: Spectral, Multispectral, Thermal.
- Rules for [PlantID]: Must start with a letter. Must not be a reserved keyword.

| File Name Example	           | Detected Plant ID	| Detected Sensor	| Destination Folder    |
|------------------------------|--------------------|-----------------|-----------------------|
| Spectral_P01_001.tiff	       | P01	              |  Spectral	      |  .../P01/Spectral/    |
| Multispectral_TestA_02.tiff  | TestA	            |  Spectral	      |  .../TestA/Spectral/  |
| Thermal_P02_14-22-05.jpg	   | P02	              |  Thermal	      |    .../P02/Thermal/   |

### 2. Fallback Detection (Default Camera Output)
Priority: Low 

If you do not rename files, the pipeline attempts to deduce the classification based on file patterns. You should avoid using the pipeline in this manner.

#### A. Multispectral Files (SILIOS)
- Logic: The script looks for a filename starting with a Word (PlantID) followed by a Date_Time pattern (_2025...) or ending with _raw.tiff / .txt.

- Constraint: The file name must start with a letter (the Plant ID).

| File Name Example             | Detected Plant ID	|  Detected Sensor |  Destination Folder  |
|-------------------------------|-------------------|------------------|----------------------|
| test_20251210_1400...raw.tiff	|  test	            |  Spectral	       | .../test/Spectral/   |
| Ble_VarieteA.txt	            |  Ble	            |  Spectral	       | .../Ble/Spectral/    |


#### B. Thermal Files (WORKSWELL)
- Logic: The script looks for filenames starting with a digit pattern HH-MM-SS-mmm (e.g., 14-20-00-123...) OR containing specific keywords (cwsi, radiometric, thermo, visible).

- Constraint: Since these files usually don't contain the Plant ID, they are sent to a holding folder.

| File Name Example             | Detected Plant ID	|  Detected Sensor |  Destination Folder        |
|-------------------------------|-------------------|------------------|----------------------------|
| 14-20-00-123-cwsi.tiff      	|  Unassigned       |  Thermal	       | .../Unassigned/Thermal/    |
| 00-10-12-402-visible.jpg      |  Unassigned       |  Thermal	       | .../Unassigned/Thermal/    |

Note: "Unassigned" thermal files will be automatically retrieved and linked to the correct plant later during the Fusion step, provided their timestamp matches a Spectral image within ±5 minutes.

### 3. Special Cases & Filtering
The pipeline includes safety nets for specific edge cases:

| Case Scenario |	File Name Example       | 	Action Taken	      | Reason                                             |
|---------------|-------------------------|-----------------------|----------------------------------------------------|
| Invalid ID    |	Spectral_01_Img.tif     |	Moved to Unassigned   | Plant ID starts with a number.                     |
| Reserved Word	| Spectral_Thermal_01.tif	| Moved to Unassigned   | "Thermal" is a reserved keyword, not a Plant ID.   |
| Artifact	    |...screenshot.jpg        |	DELETED               |	Thermal screenshot files are considered junk data. |
| Unknown       |	my_vacation.png         |	IGNORED   	          | Does not match any known sensor pattern. Left in   |
  
##  📄 File Types Handled
  
  The pipeline recognizes and processes the following formats:
  
| Extension           | Source    | Description                    | Action                                              |
|---------------------|-----------|--------------------------------|-----------------------------------------------------|
| _raw.tiff           | SILIOS    | Raw multispectral mosaic (2D)  | Demosaiced into 10 bands + Histogram extraction     |
| .txt                | SILIOS    | Acquisition Manifest           | Parsed for Exposure Time & Calibration Coefficients | 
| ...visible.jpg      | Workswell | Standard RGB photo             | Stored in GridFS                                    |
| ...radiometric.jpg  | Workswell | Thermal image with metadata    | Stored in GridFS                                    |
| ...thermo.tiff      | Workswell | Raw temperature data (16-bit)  | Stored in GridFS                                    | 
| ...cwsi.tiff        | Workswell | Crop Water Stress Index map    | Stored in GridFS                                    |
| ...screenshot.jpg   |Workswell  | User interface capture         | Deleted automatically (Junk)                        |

## 🚀 How to Use the Pipeline

### Step 1: Data Acquisition
1. Set Color Shades output folder to C:/CROPSENSE/INBOX.
2. Set the base filename to the Plant ID (e.g., P01_).
3. Capture images.
4. Copy Workswell thermal files to the same INBOX folder.

### Step 2: Run the Script

Open your Jupyter Notebook (CROPSENSE.ipynb) or Python script and execute the main function:
```Python
run_pipeline()
```

What happens next?

1. Ingestion: Files are moved from INBOX to `CROPSENSE_DATA/{Date}/{PlantID}/{Sensor}/`.
2. Processing: Spectral images are demosaiced; histograms are calculated.
3. Fusion: Thermal files are found and linked based on time.
4. Storage: Everything is saved to MongoDB.

### Step 3: Visualization & Check
You can verify the data using the provided tools:
```Python
# Check database integrity for a specific plant
check_database_integrity("P01")

# Visualize a specific spectral band (e.g., Red Edge)
show_spectral_channel("path/to/image.tiff", wavelength=756)

# Visualize a thermal map
show_thermal_image("path/to/thermo.tiff")
```

## ⚠️ Troubleshooting
- **"No database accessible"** : Check if MongoDB service is running or if the Server IP in the script (URIS_TO_TRY) is correct.
- **"Unclassified file skipped"** : The filename likely contains forbidden characters or doesn't start with a letter.
- **"Thermal: 0 files linked"** : The time difference between the Spectral and Thermal photo was greater than 300 seconds. Check camera clocks.

# Release :

## V1 : 11/12/2025

Author : Antoine Herbaux
 
