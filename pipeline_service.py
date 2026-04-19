"""
PIPELINE SERVICE - WEB TO DATA SCIENCE BRIDGE
---------------------------------------------
This file acts as the connector between the web application (Frontend/Backend)
and the core data science pipeline.

Why do we need this?
1. The web application needs to process ONE plant (sample_id) at a time, while
   the original notebook was designed to process batches of folders.
2. Web browsers cannot display Python Matplotlib windows. We must intercept
   the plots and convert them into 'Base64' string format. This allows us to
   send images directly inside a JSON response.
"""

import os
import io
import glob
import base64
import zipfile
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from sklearn.decomposition import PCA

# IMPORT THE CORE PIPELINE
# Ensure your Jupyter notebook is exported as a Python script named 'cropsense.py'
# and placed in the same directory, or accessible in your Python path.
import cropsense as cp


# =====================================================================
# PART 1: UTILITY FUNCTIONS (IMAGE CONVERSION)
# These functions take Python data and turn it into web-friendly strings.
# =====================================================================

def plot_to_base64():
    """
    Captures whatever matplotlib is currently trying to draw, saves it to a
    temporary memory buffer, and encodes it to a Base64 string.
    This prevents the server from freezing and waiting for someone to close a plot window.
    """
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()  # Clean up memory
    return img_base64


def rgb_to_base64(rgb_array):
    """
    Converts a Numpy multidimensional array (representing an image) into a PNG Base64 string.
    Used for sending the Before, After, and PCA images to the website.
    """
    # If the array is float (0.0 to 1.0), convert it to standard image format (0 to 255)
    if rgb_array.dtype in [np.float32, np.float64]:
        rgb_array = (rgb_array * 255).astype(np.uint8)

    img = Image.fromarray(rgb_array)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


# =====================================================================
# PART 2: THE "GLUE" FUNCTIONS
# These functions target specific files for a single plant (sample_id),
# overriding the batch-processing nature of the original notebook.
# =====================================================================

def get_paths_for_sample(sample_id):
    """
    Searches the database/file system to find the exact file paths
    for the Raw, Dark Reference, and White Reference HDR files for ONE specific plant.
    """
    base_dir = cp.PATH_DATA_ROOT

    for root, dirs, files in os.walk(base_dir):
        # Check if we are inside the folder for this specific sample_id
        if os.path.basename(os.path.dirname(root)) == sample_id and "Hyperspectral" in root:
            raw_files = glob.glob(os.path.join(root, "*.hdr"))

            # Separate the specific calibration files from the main capture
            raw_hdr = [f for f in raw_files if "DARKREF" not in f and "WHITEREF" not in f]
            dark_hdr = glob.glob(os.path.join(root, "*DARKREF*.hdr"))
            white_hdr = glob.glob(os.path.join(root, "*WHITEREF*.hdr"))

            if raw_hdr and dark_hdr and white_hdr:
                return raw_hdr[0], dark_hdr[0], white_hdr[0]

    raise FileNotFoundError(f"Could not find HDR hyperspectral files for {sample_id}")


def get_spectral_filepath(sample_id):
    """
    Finds the specific TIFF file needed to draw the spectral histograms/profiles.
    """
    base_dir = cp.PATH_DATA_ROOT
    for root, dirs, files in os.walk(base_dir):
        if os.path.basename(os.path.dirname(root)) == sample_id and "Spectral" in root:
            tiff_files = [f for f in files if f.endswith("_raw.tiff")]
            if tiff_files:
                return os.path.join(root, tiff_files[0])
    raise FileNotFoundError(f"Could not find spectral TIFF for {sample_id}")


def apply_pca_reduction(data, n_components=3):
    """
    Takes the massive hyperspectral cube (hundreds of bands) and uses
    Principal Component Analysis (PCA) to compress the most important data
    into just 3 bands (Red, Green, Blue) so it can be viewed on the web.
    """
    cube = data['cube']
    h, w, b = cube.shape

    # Flatten the 3D cube into 2D for the math model
    flattened_cube = cube.reshape(-1, b)

    pca = PCA(n_components=n_components)
    pca_result = pca.fit_transform(flattened_cube)

    # Reshape back to image dimensions
    pca_img = pca_result.reshape(h, w, n_components)

    # Normalize the output (scale values between 0 and 1) to create a valid image
    for i in range(n_components):
        min_val = np.min(pca_img[:, :, i])
        max_val = np.max(pca_img[:, :, i])
        pca_img[:, :, i] = (pca_img[:, :, i] - min_val) / (max_val - min_val + 1e-6)

    return pca_img


# =====================================================================
# PART 3: MAIN WEB ENDPOINTS
# These are the 3 functions your web team will call directly.
# =====================================================================

def run_pipeline(sample_id, thresholds, method, wavelength):
    """
    WEB ENDPOINT 1: Runs the analysis for a single plant and returns visual data.

    Parameters:
    - sample_id: String (e.g., "Plant_01")
    - thresholds: List of 3 numbers [min_brightness, max_brightness, ndvi_threshold]
    - method: String ("smoothing" or "standard")
    - wavelength: Float/Int (Target wavelength for specific analysis)

    Returns: JSON dictionary containing base64 images and calculated indexes.
    """
    # 1. Fetch paths
    min_b, max_b, ndvi_t = thresholds
    raw_hdr, dark_hdr, white_hdr = get_paths_for_sample(sample_id)

    # 2. Masking & Normalization (Using core pipeline logic)
    data = cp.prepare_hyperspectral_data(
        raw_hdr, dark_hdr, white_hdr,
        background='darken',
        min_brightness=min_b,
        max_brightness=max_b,
        ndvi_threshold=ndvi_t
    )

    data['mask'] = data.get('masque')

    # 3. Generate Before/After images for the UI
    # We take approximate RGB slices [110, 70, 30] from the raw cube for the 'before' picture
    before_img_b64 = rgb_to_base64(data['cube'][:, :, [110, 70, 30]])
    after_img_b64 = rgb_to_base64(data['rgb'])  # Masked result

    # 4. Calculate health indexes
    indexes_df = cp.compare_plants_indices([data], labels=[sample_id])
    indexes_dict = indexes_df.to_dict()

    # 5. Apply PCA reduction
    pca_result = apply_pca_reduction(data, n_components=3)
    pca_img_b64 = rgb_to_base64(pca_result)

    return {
        "sample_id": sample_id,
        "images": {
            "before": before_img_b64,
            "after": after_img_b64,
            "pca_reduction": pca_img_b64
        },
        "indexes": indexes_dict
    }


def plot_data(analysis, sample_id):
    """
    WEB ENDPOINT 2: Generates specific charts based on user UI selection.

    Parameters:
    - analysis: String ("profile" or "histogram")
    - sample_id: String

    Returns: JSON dictionary with the chart image encoded in Base64.
    """
    filepath = get_spectral_filepath(sample_id)

    if analysis == 'profile':
        # Tells the core pipeline to draw the line chart of spectral signatures
        cp.plot_spectral_profile(filepath, smooth=True)
        plot_b64 = plot_to_base64()  # Intercept the drawing and save to text

    elif analysis == 'histogram':
        # Tells the core pipeline to draw the distribution of pixel intensities
        cp.plot_full_spectral_histogram(filepath, mode='overlay')
        plot_b64 = plot_to_base64()

    else:
        raise ValueError("Analysis parameter must be 'profile' or 'histogram'")

    return {
        "sample_id": sample_id,
        "analysis_type": analysis,
        "plot_image_base64": plot_b64
    }


def process_zip_upload(zip_file_path):
    """
    WEB ENDPOINT 3: Handles new incoming plant data.
    Unzips the file, sorts the contents into the correct folders, pushes
    metadata to the NoSQL MongoDB database, and returns the newly generated ID.
    """
    inbox_dir = cp.PATH_INBOX
    os.makedirs(inbox_dir, exist_ok=True)

    # 1. Unpack the uploaded ZIP file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(inbox_dir)

    # 2. Trigger the core pipeline's sorting logic
    cp.organize_incoming_files()

    # 3. Database Ingestion
    # Because full processing is heavy, we only trigger the DB insert for new files.
    # We use the MongoDB client established in the core pipeline to log the capture event.
    db_client = cp.get_mongo_client()
    if db_client:
        db = db_client[cp.DB_NAME]

        # Look at the most recent event to figure out what sample_id was just created
        latest_event = db['capture_events'].find_one(sort=[("timestamp", -1)])

        if latest_event:
            return latest_event.get('sample_id', 'Unknown')

    return "Error: Could not determine sample_id after unzip"