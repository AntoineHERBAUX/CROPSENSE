# CROPSENSE Data Processing Platform (V1.2.1)

## 📌 Project Overview
  Version: 1.2.1
  
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
3. Make sure both your cameras have the right date and hour
4. Capture images.
5. Copy Workswell thermal files to the same INBOX folder.

### Step 2: Run the Script

Open your Jupyter Notebook (`CROPSENSE.ipynb`) or Python script and execute the main function:
```python
run_pipeline()
```

#### 🔄 How the File Linking Works (The "Fusion" Logic)
The pipeline uses a **temporal clustering algorithm** to automatically link your Spectral and Thermal images. It does not rely on filenames matching perfectly, but rather on the **timestamps** of the files.

1.  Trigger: The process starts when the script finds a raw spectral image (e.g., `.../P01/Spectral/image_raw.tiff`).
2.  Target Search: It calculates the creation time of that spectral image. Then, it looks into the corresponding `Thermal` folder for that specific Plant ID (e.g., `.../P01/Thermal/`).
3.  Time Matching: It scans all files in that thermal folder and selects those captured within a **±300 seconds (5 minutes)** tolerance window of the spectral image.
4.  Clustering: It groups the following 4 file types together into a single database entry "event":
    * Visual RGB: (Standard camera photo from the thermal sensor)
    * Radiometric JPEG: (Thermal image with embedded temperature data)
    * Raw Thermal TIFF: (Raw temperature data matrix)
    * CWSI TIFF: (Crop Water Stress Index map)

> **Note:** If a thermal file is found but is outside the 5-minute window, it is considered an "Independent Thermal Event" and saved separately.


### Step 3: Visualization & Analysis Tools

You can verify the data using the provided visualization functions. These tools allow you to inspect the quality of the data directly from the raw files or the database exports.

#### 1. Database Diagnosis
**Function:** `check_database_integrity(plant_id)`
* **What it does:** Verifies that the files for a specific plant have been correctly uploaded to the MongoDB GridFS storage.
* **Output:** It prints a report showing the file size and ID for the Spectral RAW file and all 4 linked Thermal files.
```python
check_database_integrity("P01")
```

#### 2. Spectral Channel Inspection
**Function:** `show_spectral_channel(filepath, wavelength=756)`
* **What it does:** Extracts and displays a *single* specific band from the multispectral TIFF.
* **Features:**
    * You can select the band by index (`0-9`) or by wavelength (e.g., `wavelength=756` for Red Edge).
    * It automatically handles Raw Mosaics (by demosaicing on the fly) or pre-processed 3D Stacks.
    * Displays a heat map of pixel intensity.
```python
show_spectral_channel("path/to/spectral_raw.tiff", wavelength=557) # Green Peak
```

#### 3. Thermal Image Analysis
**Function:** `show_thermal_image(filepath)`
* **What it does:** Renders the 16-bit raw thermal data into a viewable color map.
* **Features:**
    * **Temperature Mode:** Uses the 'Magma' palette (Black/Purple=Cold, Orange/Yellow=Hot).
    * **CWSI Mode:** Automatically detects Crop Water Stress Index files and uses a 'Red-Green' traffic light palette (Red=High Stress).
    * **Statistics:** Prints the Min, Max, and Mean temperature (or index value) of the image.
```python
show_thermal_image("path/to/thermal_raw.tiff")
```

#### 4. Exposure Check (Single Band)
**Function:** `plot_image_histogram(filepath, band_index, bins, log_scale)`
* **What it does:** Plots the distribution of pixel intensities for a single band or thermal image.
* **Why use it:** To check for under-exposure (too dark) or saturation (too bright/clipped pixels) in a specific wavelength.
```python
# Check the exposure of the Near Infrared band (Band 9)
plot_image_histogram("path/to/spectral.tiff", band_index=9)
```

#### 5. Full Spectral Quality Check
**Function:** `plot_full_spectral_histogram(filepath, mode='overlay')`
* **What it does:** Analyzes the dynamic range of the *entire* multispectral cube.
* **Modes:**
    * `'overlay'`: Plots 10 separate lines (one per band) on the same graph to compare sensor response across wavelengths.
    * `'global'`: Aggregates all pixels into one giant histogram to see overall sensor usage.
```python
plot_full_spectral_histogram("path/to/spectral.tiff", mode='overlay')
```

#### 6. Spectral Signature (Reflectance Profile)
**Function:** `plot_spectral_profile(filepath, smooth=True)`
* **What it does:** Calculates the mean intensity of the plant for each of the 10 wavelengths and plots the curve.
* **Why use it:** This is the "fingerprint" of the plant. Healthy plants typically show a "Green Peak" at 557nm and a sharp rise in the "Red Edge" (756nm+).
```python
plot_spectral_profile("path/to/spectral.tiff")
```

#### 7. Data Export
**Function:** `export_analysis_to_csv(filepath, output_csv, analysis_type)`
* **What it does:** Instead of a graph, this generates a CSV file with the raw numerical data, which you can open in Excel.
* **Options:**
    * `analysis_type='profile'`: Exports the Spectral Signature (Wavelength vs Intensity).
    * `analysis_type='histogram'`: Exports the histogram counts for all 10 bands.
```python
export_analysis_to_csv("path/to/image.tiff", "my_results.csv", analysis_type="profile")
```

## ❓ Quick Helper / Cheat Sheet

Here are the answers to the most common questions when using the CROPSENSE pipeline.

### 1. How do I process my data and put it into the database?
**Answer:** Put your files in the `INBOX` folder and run the main pipeline.
```python
run_pipeline()
```

### 2. How do I verify if a specific plant (e.g., P01) was saved correctly?
**Answer:** Use the integrity check function with the Plant ID.
```python
check_database_integrity("P01")
```

### 3. How do I view a specific spectral band (like Red Edge or Green)?
**Answer:** Use `show_spectral_channel`. You can specify the wavelength (e.g., 557 for Green, 756 for Red Edge).
```python
show_spectral_channel("path/to/spectral.tiff", wavelength=756)
```

### 4. How can I see the Thermal or Water Stress (CWSI) map?
**Answer:** Use `show_thermal_image`. It automatically detects if it's a temperature map or a CWSI traffic-light map.
```python
show_thermal_image("path/to/thermal.tiff")
```

### 5. How do I check if my photo is too dark (underexposed) or too bright (saturated)?
**Answer:** Plot the histogram for that specific band. If the curve touches the left (0) it's too dark; if it touches the right, it's saturated.
```python
# Check Band 9 (NIR)
plot_image_histogram("path/to/spectral.tiff", band_index=9)
```

### 6. How can I see the spectral signature of the plant?
**Answer:** Use the profile plotter to see the curve of intensity across all 10 wavelengths.
```python
plot_spectral_profile("path/to/spectral.tiff")
```

### 7. How do I compare the quality of all 10 bands at once?
**Answer:** Use the full spectral histogram in 'overlay' mode.
```python
plot_full_spectral_histogram("path/to/spectral.tiff", mode='overlay')
```

### 8. How do I get the data out of Python and into Excel?
**Answer:** Use the export function to save the analysis as a CSV file.
```python
export_analysis_to_csv("path/to/image.tiff", output_csv="my_data.csv", analysis_type="profile")
```

### 9. Why are my Thermal files not showing up with the Spectral ones?
**Answer:** The script links them based on time. They must be taken within **5 minutes (300 seconds)** of the spectral photo. If they are further apart, they are saved as "Independent Thermal Events".

### 10. Where do my files go after I run the script?
**Answer:** They are moved from the `INBOX` to the `CROPSENSE_DATA` folder, organized by Date, Plant ID, and Sensor type:
`CROPSENSE_DATA / 2023-12-10 / P01 / Spectral / ...`

### 11. My files are being skipped / ignored. How should I name them?
**Answer:** The pipeline uses strict pattern matching. Your files **MUST** start with the Plant ID, followed by the Date and Time.
* **Format:** `PlantID_YYYYMMDD_HHMMSS_....tiff`
* **Example:** `P01_20231210_143000_raw.tiff`
* **Bad Name:** `image_01.tiff` (This will be ignored).

### 12. Can I change the 5-minute time window for linking Thermal images?
**Answer:** Yes. Open `CROPSENSE.ipynb` and search for the `find_thermal_cluster` function.
Change the `tolerance` value (in seconds):

```python
# Change 300 (5 mins) to 60 (1 min) or 600 (10 mins)
def find_thermal_cluster(..., tolerance=300):
```

### 13. How do I delete a specific plant or bad entry from the database?
Answer: The script does not delete data to prevent accidents. To delete data:
1. Open MongoDB Compass.
2. Navigate to the CROPSENSE_DB database.
3. Find the document with the specific plant_id and timestamp.
4. Click the trash icon to remove it manually.

### 14. My Thermal files don't have a prefix (e.g., just 20231210...). How do I add the Plant ID?
Answer: You can use the batch rename tool to add a prefix to all files in a folder. This is useful if your camera saves files without the plant name.

```python

# Add "P01_" to all files in the thermal folder
# This changes "20231210.tiff" -> "P01_20231210.tiff"
rename_batch_prefix("C:/CROPSENSE/INBOX/Thermal", old_prefix="", new_prefix="P01")

```

### 15. I'm getting a connection timeout error with MongoDB. What should I do?

**Answer:** Check that MongoDB is running.

**Important:** The script is configured to try multiple addresses (`URIS_TO_TRY`).

> **Special Note:** If you are on the school network (e.g., Junia), the firewall may be blocking the connection. Try using `localhost` or a connection outside the school domain.

### 16. Can I change the location of the folders (INBOX, Data)?

**Answer:** Yes, the paths are defined at the beginning of the script.

Find and modify these variables in the first cell of code:
```python
BASE_DIR = "C:/CROPSENSE" # Change this to your disk (e.g., "D:/PROJET")
INBOX_DIR = os.path.join(BASE_DIR, "INBOX")
```
### 17. Does the script work with standard JPG or PNG images?

**Answer:** No. The pipeline, as for now, is designed specifically for scientific analysis.

Spectral: Requires .tiff (16-bit) files.
Thermal: Requires .tiff (raw data) or radiometric (Workswell) .jpg files.
Standard images (phone photos) will be ignored or will cause errors during spectral analysis.


# Release :


## V1.2.1 : 14/12/2025
Now csv file can be generated from histogram and profile
## V1.2 : 13/12/2025
Full histogram integration.
## V1.1 : 13/12/2025 
Fixed an issue where any thermic files could be associated with a spectral file, no matter the id.
Now thermic files can be send apart from spectral files
## V1 : 11/12/2025

Author : Antoine Herbaux
 
