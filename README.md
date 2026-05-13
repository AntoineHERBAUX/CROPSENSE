# CROPSENSE Data Processing Platform (V2)

## 📌 Project Overview
Version: 2.0
  
Context: CROPSENSE Project - Phase 2
  
Objective: Early detection of plant leaf diseases using multispectral and thermal imaging. This repository contains the automated ETL (Extract, Transform, Load) pipeline designed to ingest, process, and store high-throughput phenotyping data. It bridges the gap between raw camera output (SILIOS, Workswell, & SPECIM) and a structured MongoDB database, preparing the data for subsequent AI analysis.
  
## 🛠️ Prerequisites & Setup
Before running the pipeline, ensure your environment is correctly configured.
  
### 1. Hardware Requirements
#### Computer: 
Windows Laptop/PC (Project Laptop).
  
#### Cameras: 
* Multispectral: SILIOS CMS4/TOUCAN (USB).
* Thermal: Workswell WIRIS Agro R (USB/SD Card).
* Hyperspectral: SPECIM (External).
  
#### Network: 
Access to the local server (if applicable. Note: Junia Firewall blocks utilisation of MongoDB between differents PC/Servers) or `localhost`.
  
### 2. Software Installation
You need Python 3.10+ and a MongoDB server running.
  
#### Install Python Libraries:
Open your terminal (Command Prompt) and run: 
`pip install numpy pandas pymongo matplotlib opencv-python tifffile imagecodecs spectral scipy --user`

#### Setup MongoDB: 
1. Install MongoDB Community Server.
2. Install MongoDB Compass (for visualization).
3. Ensure the MongoDB service is running (Task Manager > Services).

### 3. Folder Structure
Create the following folders on your C: drive (or configure paths in the script):

#### C:/CROPSENSE/INBOX 
*The "Drop Zone". Configure your camera software (Color Shades) to save images here*.

#### C:/CROPSENSE/CROPSENSE_DATA 
*The "Safe Storage". The script will automatically organize processed files here.*

---

## 📁 File Naming & Classification Rules

The pipeline uses a Priority Logic to classify files. It first looks for an Explicit Prefix (recommended for perfect sorting). If none is found, it falls back to Pattern Recognition to guess the file type and owner. Tip: Try to keep the same logic on naming sample.

### 1. Explicit Naming (Recommended)
Priority: High 

Use this format to force the pipeline to sort files exactly where you want them.

* **Format**: `[SensorType]_[PlantID]_[FreeText].ext`
* **Keywords for [SensorType]**: Spectral, Multispectral, Thermal, Hyperspectral.
* **Rules for [PlantID]**: Must start with a letter. Must not be a reserved keyword.

| File Name Example | Detected Plant ID | Detected Sensor | Destination Folder |
| :--- | :--- | :--- | :--- |
| Spectral_P01_001.tiff | P01 | Spectral | .../P01/Spectral/ |
| Multispectral_TestA_02.tiff | TestA | Spectral | .../TestA/Spectral/ |
| Thermal_P02_14-22-05.jpg | P02 | Thermal | .../P02/Thermal/ |

### 2. Fallback Detection (Default Camera Output)
Priority: Low 

If you do not rename files, the pipeline attempts to deduce the classification based on file patterns. You should avoid using the pipeline in this manner.

#### A. Multispectral Files (SILIOS)
* **Logic**: The script looks for a filename starting with a Word (PlantID) followed by a Date_Time pattern (`_2025...`) or ending with `_raw.tiff` / `.txt`.
* **Constraint**: The file name must start with a letter (the Plant ID).

#### B. Thermal Files (WORKSWELL)
* **Logic**: The script looks for filenames starting with a digit pattern `HH-MM-SS-mmm` (e.g., `14-20-00-123...`) OR containing specific keywords (`cwsi`, `radiometric`, `thermo`, `visible`).
* **Constraint**: Since these files usually don't contain the Plant ID, they are sent to a holding folder.

> Note: "Unassigned" thermal files will be automatically retrieved and linked to the correct plant later during the Fusion step, provided their timestamp matches a Spectral image within a specific time window.

### 3. Special Cases & Filtering
The pipeline includes safety nets for specific edge cases:

| Case Scenario | File Name Example | Action Taken | Reason |
| :--- | :--- | :--- | :--- |
| Invalid ID | Spectral_01_Img.tif | Moved to Unassigned | Plant ID starts with a number. |
| Reserved Word | Spectral_Thermal_01.tif | Moved to Unassigned | "Thermal" is a reserved keyword, not a Plant ID. |
| Artifact | ...screenshot.jpg | DELETED | Thermal screenshot files are considered junk data. |
| Calibration | ...DARKREF.hdr | IGNORED | Dark/White references are for calibration only. |
| Unknown | my_vacation.png | IGNORED | Does not match any known sensor pattern. |

---

## 📄 File Types Handled
  
The pipeline recognizes and processes the following formats:
  
| Extension | Source | Description | Action |
| :--- | :--- | :--- | :--- |
| `_raw.tiff` | SILIOS | Raw multispectral mosaic (2D) | Demosaiced into 10 bands + Histogram extraction |
| `.txt` | SILIOS | Acquisition Manifest | Parsed for Exposure Time & Normalization Coefficients | 
| `.hdr / .raw` | SPECIM | Hyperspectral Data Cube | Calibrated (Dark/White), stored as a multi-file bundle |
| `...visible.jpg` | Workswell | Standard RGB photo | Stored in GridFS |
| `...radiometric.jpg` | Workswell | Thermal image with metadata | Stored in GridFS |
| `...thermo.tiff` | Workswell | Raw temperature data (16-bit)| Stored in GridFS | 
| `...cwsi.tiff` | Workswell | Crop Water Stress Index map | Stored in GridFS |
| `...screenshot.jpg`| Workswell | User interface capture | Deleted automatically (Junk) |

---

## 🚀 How to Use the Pipeline

### Step 1: Data Acquisition
1. Set Color Shades output folder to `C:/CROPSENSE/INBOX`.
2. Set the base filename to the Plant ID (e.g., `P01_`).
3. Make sure both your cameras have the right date and hour.
4. Capture images.
5. Copy Workswell thermal files to the same INBOX folder.

### Step 2: Run the Script
Open your Jupyter Notebook (`CROPSENSE.ipynb`) or Python script and execute the main function:
```python
run_pipeline()
```
#### 🔄 How the File Linking Works (The "Fusion" Logic)
The pipeline uses a temporal clustering algorithm to automatically link your Spectral and Thermal images. It does not rely on filenames matching perfectly, but rather on the timestamps of the files.

1. **Trigger:** The process starts when the script finds a raw spectral image (e.g., `.../P01/Spectral/image_raw.tiff`).
2. **Target Search:** It calculates the creation time of that spectral image. Then, it looks into the corresponding Thermal folder for that specific Plant ID.
3. **Time Matching:** It scans all files in that thermal folder and selects those captured within a tolerance window (default ±5 minutes).
4. **Clustering:** It groups Visual RGB, Radiometric JPEG, Raw Thermal TIFF, and CWSI TIFF together into a single database entry.

> **Note:** If a thermal file is found but is outside the time window, it is considered an "Independent Thermal Event" and saved separately.

---

### Step 3: Visualization & Analysis Tools
You can verify the data using the provided visualization functions.

#### 1. Database Diagnosis
**Function:** `check_database_integrity(plant_id)`
* **What it does:** Verifies that the files for a specific plant have been correctly uploaded to the MongoDB GridFS storage.
* **Output:** It prints a report showing the file size and ID for the Spectral RAW file and all linked Thermal files.

#### 2. Spectral Channel Inspection
**Function:** `show_spectral_channel(filepath, wavelength=756)`
* **What it does:** Extracts and displays a single specific band from the multispectral TIFF.
* **Features:**
  * You can select the band by index (`0-9`) or by wavelength (e.g., `wavelength=756` for Red Edge).
  * It automatically handles Raw Mosaics (by demosaicing on the fly), pre-processed SILIOS 10-band Stacks, or external 125-band stacks.

#### 3. Thermal Image Analysis
**Function:** `show_thermal_image(filepath)`
* **What it does:** Renders the 16-bit raw thermal data into a viewable color map.
* **Features:**
  * **Temperature Mode:** Uses the 'Magma' palette (Black/Purple=Cold, Orange/Yellow=Hot).
  * **CWSI Mode:** Automatically detects Crop Water Stress Index files and uses a 'Red-Green' traffic light palette.
  * **Statistics:** Prints the Min, Max, and Mean temperature (or index value) of the image.

#### 4. Exposure Check (Single Band)
**Function:** `plot_image_histogram(filepath, band_index, bins, log_scale)`
* **What it does:** Plots the distribution of pixel intensities for a single band or thermal image.

#### 5. Full Spectral Quality Check
**Function:** `plot_full_spectral_histogram(filepath, mode='overlay')`
* **What it does:** Analyzes the dynamic range of the entire multispectral cube.
* **Modes:**
  * `'overlay'`: Plots separate lines (one per band) on the same graph to compare sensor response across wavelengths.
  * `'global'`: Aggregates all pixels into one single histogram.

#### 6. Spectral Signature (Reflectance Profile)
**Function:** `plot_spectral_profile(filepath, smooth=True)`
* **What it does:** Calculates the mean intensity of the plant for each wavelength and plots the curve.
* **Smoothing:** If `smooth=True`, it uses spline interpolation to draw a curved "fingerprint" rather than jagged straight lines.

#### 7. Hyperspectral Preparation & Index Mapping
* **Calibration:** `prepare_hyperspectral_data(raw_hdr_path, dark_hdr_path, white_hdr_path)` performs radiometric correction and is memory-optimized to prevent Jupyter crashes on large files.
* **Index Mapping:** `show_index_map(data, index_name="NDVI")` generates a heat map for specific indices. Supported indices include NDVI, GNDVI, RVI, WI, NDWI, SIPI, PRI, ARI, and CARI.

#### 8. Advanced Hyperspectral Analysis
* **Compare Plants:** `show_multiple_hyperspectral_graphs(data_list, labels)` plots multiple spectral profiles on the same graph.
* **Index Table:** `compare_plants_indices(data_list, labels)` generates a Pandas DataFrame comparing the 9 standard health indices across different plants.
* **Custom Index:** `create_custom_index(data, index_name, formula_str, bands_dict)` lets you calculate a completely custom index using a text formula (e.g., `"(L1 - L2) / L3"`).

#### 9. Data Export
**Function:** `export_analysis_to_csv(filepath, output_csv, analysis_type)`
* **What it does:** Generates a CSV file with the raw numerical data for Excel analysis.
* **Options:**
  * `analysis_type='profile'`: Exports the Mean Intensity vs Wavelength.
  * `analysis_type='histogram'`: Exports the Pixel Counts vs Intensity for all bands.

---

## ❓ Quick Helper / Cheat Sheet
Here are the answers to the most common questions when using the CROPSENSE pipeline.

1. **How do I process my data and put it into the database?**
   * **Answer:** Put your files in the `INBOX` folder and run `run_pipeline()`.

2. **How do I verify if a specific plant (e.g., P01) was saved correctly?**
   * **Answer:** Use `check_database_integrity("P01")`.

3. **How do I view a specific spectral band (like Red Edge or Green)?**
   * **Answer:** Use `show_spectral_channel("path/to/spectral.tiff", wavelength=756)`.

4. **How can I see the Thermal or Water Stress (CWSI) map?**
   * **Answer:** Use `show_thermal_image("path/to/thermal.tiff")`.

5. **How do I get an index table comparing multiple plants?**
   * **Answer:** Use `compare_plants_indices([data1, data2], labels=["Healthy", "Stressed"])`.

6. **What do the different Spectral Indices mean?**
   * **Answer:** Run `explain_spectral_index("ALL")` to see a detailed breakdown of formulas, purposes, and typical values for healthy vs. diseased plants.

7. **Can I create my own mathematical index?**
   * **Answer:** Yes. Use `create_custom_index` to define a formula string like `"(A - B) / C"` mapped to specific wavelengths.

8. **How do I check if my photo is under/overexposed?**
   * **Answer:** Use `plot_image_histogram("path/to/spectral.tiff", band_index=9)`.

9. **How do I compare the quality of all bands at once?**
   * **Answer:** Use `plot_full_spectral_histogram("path/to/spectral.tiff", mode='overlay')`.

10. **How do I get the data out of Python and into Excel?**
    * **Answer:** Use `export_analysis_to_csv("path/to/image.tiff", output_csv="my_data.csv", analysis_type="profile")`.

11. **Why are my Thermal files not showing up with the Spectral ones?**
    * **Answer:** The script links them based on time. They must be taken within the specified time window of the spectral photo.

12. **Where do my files go after I run the script?**
    * **Answer:** They are moved from the `INBOX` to the `CROPSENSE_DATA` folder, organized by Date, Plant ID, and Sensor type.

13. **My files are being skipped / ignored. How should I name them?**
    * **Answer:** The pipeline uses strict pattern matching. Your files MUST start with the Plant ID, followed by the Date and Time.

14. **How do I delete a specific plant or bad entry from the database?**
    * **Answer:** The script does not delete data to prevent accidents. You can delete data manually via MongoDB Compass.

15. **I'm getting a connection timeout error with MongoDB. What should I do?**
    * **Answer:** Check that MongoDB is running. The script is configured to try multiple addresses (`URIS_TO_TRY`). If you are on a school network, try using `localhost`.

16. **Can I change the location of the folders (INBOX, Data)?**
    * **Answer:** Yes, the paths are defined at the beginning of the script (`BASE_DIR`, `INBOX_DIR`).

17. **Does the script work with standard JPG or PNG images?**
    * **Answer:** No. The pipeline is designed specifically for scientific analysis using `.tiff` or radiometric `.jpg` files.

---

## 📅 Release History

### V2.0 : 23/04/2026
* Hyperspectral fully implemented and improved file naming rules.
* CROPSENSE_ML_Test.ipynb contains tests models integration

### V1.2.1 : 14/12/2025
* Now csv file can be generated from histogram and profile.

### V1.2 : 13/12/2025
* Full histogram integration.

### V1.1 : 13/12/2025
* Fixed an issue where any thermic files could be associated with a spectral file, no matter the id.
* Now thermic files can be send apart from spectral files.

### V1 : 11/12/2025
* Initial Release.

**Authors : Antoine Herbaux and Olesia Yankiv**
