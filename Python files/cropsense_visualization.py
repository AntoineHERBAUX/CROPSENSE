import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt



def show_spectral_channel(filepath, channel_index=None, wavelength=None, interpolation='bicubic'):
    """
    Displays a specific channel from a SILIOS multispectral TIFF file.
    
    Parameters:
    - filepath (str): Path to the .tiff file (Raw Mosaic or Stack).
    - channel_index (int): Index of the band (0 to 9, or 0 to 125).
    - wavelength (str/int): Wavelength to find (e.g., 557 or "557nm"). 
                            Overrides channel_index if provided.
    """
    
# 1. Resolve Channel Index from Wavelength
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    # 1. Charger l'image D'ABORD pour connaître sa structure
    try:
        img_data = tiff.imread(filepath)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    is_125_bands = (img_data.ndim == 3 and img_data.shape[2] == 125)

    # 2. Résoudre le channel_index si une longueur d'onde est fournie
    if wavelength is not None:
        target_wl = float(str(wavelength).replace("nm", "").strip())
        
        if is_125_bands:
            # Formule inversée : Index = (Wavelength - 450) / (500 / 124)
            step = 500 / 124
            calculated_idx = int(round((target_wl - 450) / step))
            channel_index = max(0, min(124, calculated_idx)) # Garder entre 0 et 124
            print(f"🔍 Wavelength {target_wl}nm correspond to channel index {channel_index}")
        else:
            # Logique d'origine pour SILIOS (10 bandes)
            found = False
            for idx, name in SILIOS_WAVELENGTHS.items():
                if str(int(target_wl)) in name:
                    channel_index = idx
                    found = True
                    break
            if not found:
                print(f"❌ Wavelength '{wavelength}' not found in SILIOS.")
                return

    if channel_index is None:
        print("❌ Invalid channel index.")
        return

    # 3. Extraction de l'image
    band_image = None
    if is_125_bands:
        band_image = img_data[:, :, channel_index]
        mode = "External Stack (125 Bands)"
        # Calcul de la longueur d'onde exacte pour l'affichage
        wl_display = f"{450 + channel_index * (500 / 124):.1f} nm"
        
    elif img_data.ndim == 3 and img_data.shape[0] < img_data.shape[1]:
        band_image = img_data[channel_index]
        mode = "Processed Stack (Silios)"
        wl_display = SILIOS_WAVELENGTHS.get(channel_index, f"Canal {channel_index}")
        
    elif img_data.ndim == 2:
        if channel_index not in TOUCAN_PATTERN: return
        h, w = img_data.shape
        new_h, new_w = h // 4, w // 4
        stack = [img_data[r::4, c::4][:new_h, :new_w] for r, c in TOUCAN_PATTERN[channel_index]]
        band_image = np.mean(stack, axis=0)
        mode = "Raw Mosaic (Silios)"
        wl_display = SILIOS_WAVELENGTHS.get(channel_index, f"Canal {channel_index}")

    # 4. Affichage
    plt.figure(figsize=(8, 8))
    plt.title(f"Spectral Image: {wl_display}\nMode: {mode}")
    img_plot = plt.imshow(band_image, cmap='inferno', interpolation=interpolation) # Lissage ajouté ici !
    plt.colorbar(img_plot, label="Pixel Intensity")
    plt.axis('off') 
    plt.show()

def show_spectral_image(filepath, r_wl=650, g_wl=550, b_wl=450, r_idx=None, g_idx=None, b_idx=None, interpolation='bicubic'):
    """
    Affiche une composition RGB (vraies couleurs) depuis un fichier TIFF multispectral.
    
    Parameters:
    - r_wl, g_wl, b_wl : Longueurs d'ondes cibles pour le Rouge, Vert, Bleu.
    - r_idx, g_idx, b_idx : Permet de forcer des index de canaux spécifiques si besoin.
    """
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    # 1. Charger l'image D'ABORD pour connaître sa structure
    try:
        img_data = tiff.imread(filepath)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    is_125_bands = (img_data.ndim == 3 and img_data.shape[2] == 125)

    # 2. Fonction utilitaire pour trouver l'index exact d'une longueur d'onde
    def get_channel_index(target_wl, fallback_idx):
        if is_125_bands:
            # Formule pour le dataset 450-950nm
            step = 500 / 124
            calculated_idx = int(round((target_wl - 450) / step))
            return max(0, min(124, calculated_idx))
        else:
            # Recherche dans le dictionnaire SILIOS
            for idx, name in SILIOS_WAVELENGTHS.items():
                if str(int(target_wl)) in name:
                    return idx
            return fallback_idx # Si non trouvé, on utilise l'index de secours

    # Résolution des 3 canaux (on utilise des index de secours au cas où pour SILIOS)
    idx_R = r_idx if r_idx is not None else get_channel_index(r_wl, fallback_idx=5)
    idx_G = g_idx if g_idx is not None else get_channel_index(g_wl, fallback_idx=3)
    idx_B = b_idx if b_idx is not None else get_channel_index(b_wl, fallback_idx=1)

    print(f"🔍 RGB Composé avec les canaux - R:{idx_R}, G:{idx_G}, B:{idx_B}")

    # 3. Fonction pour extraire un canal spécifique selon le format
    def extract_band(channel_index):
        if is_125_bands:
            return img_data[:, :, channel_index]
        elif img_data.ndim == 3 and img_data.shape[0] < img_data.shape[1]:
            return img_data[channel_index]
        elif img_data.ndim == 2:
            if channel_index not in TOUCAN_PATTERN: 
                return np.zeros((img_data.shape[0]//4, img_data.shape[1]//4))
            h, w = img_data.shape
            stack = [img_data[r::4, c::4][:h//4, :w//4] for r, c in TOUCAN_PATTERN[channel_index]]
            return np.mean(stack, axis=0)
        return None

    # Extraction des 3 matrices 2D
    band_R = extract_band(idx_R)
    band_G = extract_band(idx_G)
    band_B = extract_band(idx_B)

    if band_R is None or band_G is None or band_B is None:
        print("❌ Erreur lors de l'extraction des canaux.")
        return

    # 4. Superposition et Normalisation
    # On empile les 3 matrices pour faire un cube (H, W, 3) compatible RGB
    rgb_image = np.dstack((band_R, band_G, band_B))
    
    # La normalisation "intelligente" (Percentile 2% - 98%)
    # Évite que l'image soit gâchée par un seul pixel brillant ou trop sombre
    p2, p98 = np.percentile(rgb_image, (2, 98))
    rgb_normalized = np.clip((rgb_image - p2) / (p98 - p2), 0, 1)

    mode = "External Stack (125 Bands)" if is_125_bands else ("Raw Mosaic (Silios)" if img_data.ndim == 2 else "Processed Stack (Silios)")

    # 5. Affichage
    plt.figure(figsize=(8, 8))
    plt.title(f"RGB True Color Composite\nMode: {mode} | Wavelengths ~ {r_wl}nm, {g_wl}nm, {b_wl}nm")
    
    # Pas de cmap='inferno' ici, car on affiche une vraie image RGB couleur !
    plt.imshow(rgb_normalized, interpolation=interpolation)
    plt.axis('off') 
    plt.show()
 

def show_thermal_image(filepath):
    """
    Displays a thermal image (Raw TIFF or CWSI) with a color scale.
    Also prints statistics (Min, Max, Mean) of the temperature/index.
    
    Parameters:
    - filepath (str): Path to the .tiff file (e.g., '..._thermo.tiff' or '..._cwsi.tiff')
    """
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    try:
        # 1. Read Image
        # For thermal, it's a simple 2D image (1 channel), not a cube.
        img_data = tiff.imread(filepath)
        
        # 2. Detect Type (Temperature or CWSI)
        filename = os.path.basename(filepath).lower()
        
        if "cwsi" in filename:
            # CWSI is an index between 0 and 1 (or 0-100%)
            label_unit = "CWSI Index (Water Stress)"
            cmap_choice = "RdYlGn_r" # Red = High Stress, Green = Healthy
        else:
            # Raw Thermo
            label_unit = "Raw Value (Temperature)"
            cmap_choice = "magma" # Black/Purple = Cold, Orange/Yellow = Hot
            
        # 3. Calculate Statistics
        val_min = np.min(img_data)
        val_max = np.max(img_data)
        val_avg = np.mean(img_data)
        
        print(f"📊 Statistics for {filename}:")
        print(f"   🔹 Min: {val_min:.2f}")
        print(f"   🔸 Max: {val_max:.2f}")
        print(f"   sz Mean: {val_avg:.2f}")

        # 4. Graphical Display
        plt.figure(figsize=(10, 8))
        plt.title(f"Thermal Analysis: {filename}")
        
        # Display with false colors
        img_plot = plt.imshow(img_data, cmap=cmap_choice)
        
        # Side Colorbar
        cbar = plt.colorbar(img_plot)
        cbar.set_label(label_unit, rotation=270, labelpad=15)
        
        plt.axis('off')
        plt.show()

    except Exception as e:
        print(f"❌ Error during display: {e}")


def plot_image_histogram(filepath, band_index=None, bins=100, log_scale=False):
    """
    Displays the pixel intensity distribution histogram for a given image.
    Handles both Spectral images (selectable band) and Thermal images.
    
    Parameters:
    - filepath (str): Path to the .tiff file.
    - band_index (int, optional): Band index (0-9) for spectral files. Ignored for thermal.
    - bins (int): Number of bars in the histogram (default 100).
    - log_scale (bool): If True, uses a logarithmic scale (useful if background dominates).
    """
    
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    try:
        img_data = tiff.imread(filepath)
        data_to_plot = None
        title_suffix = ""
        color = 'gray'

        # --- CASE 1: PROCESSED 3D CUBE (Bands, H, W) ---
        if img_data.ndim == 3 and img_data.shape[0] < img_data.shape[1]:
            if band_index is None: band_index = 0
            if band_index >= img_data.shape[0]:
                print(f"❌ Invalid band index ({band_index}).")
                return

            data_to_plot = img_data[band_index].flatten()
            wl = SILIOS_WAVELENGTHS.get(band_index, f"Band {band_index}")
            title_suffix = f"- Spectral {wl} (Processed)"
            color = 'purple'

        # --- CASE 1.5: EXTERNAL DATASET (H, W, Bands) ---
        elif img_data.ndim == 3 and img_data.shape[2] > 1:
            if band_index is None: band_index = 0
            if band_index >= img_data.shape[2]:
                print(f"❌ Invalid band index ({band_index}).")
                return
            
            data_to_plot = img_data[:, :, band_index].flatten()
            wl = SILIOS_WAVELENGTHS.get(band_index, f"Band {band_index}")
            title_suffix = f"- Spectral {wl} (External Data)"
            color = 'purple'

        # --- CASE 2: RAW 2D MOSAIC OR THERMAL ---
        elif img_data.ndim == 2:
            if "thermo" in filepath.lower() or "cwsi" in filepath.lower():
                data_to_plot = img_data.flatten()
                title_suffix = "- Thermal Data"
                color = 'orange'
            elif band_index is not None:
                if band_index not in TOUCAN_PATTERN:
                    print("❌ Error: Invalid band index for RAW Mosaic")
                    return
                r_off = band_index // 4
                c_off = band_index % 4
                data_to_plot = img_data[r_off::4, c_off::4].flatten()
                wl = SILIOS_WAVELENGTHS.get(band_index, f"Band {band_index}")
                title_suffix = f"- Spectral {wl} (Extracted from RAW)"
                color = 'blue'
            else:
                data_to_plot = img_data.flatten()
                title_suffix = "- Full Raw Mosaic (Mixed)"
                color = 'black'
        else:
            print(f"❌ Unrecognized format with shape: {img_data.shape}")
            return

        plt.figure(figsize=(10, 6))
        mean_val = np.mean(data_to_plot)
        median_val = np.median(data_to_plot)
        
        plt.hist(data_to_plot, bins=bins, color=color, alpha=0.7, log=log_scale, edgecolor='black', linewidth=0.5)
        plt.axvline(mean_val, color='red', linestyle='dashed', linewidth=1.5, label=f'Mean: {mean_val:.2f}')
        plt.axvline(median_val, color='yellow', linestyle='dotted', linewidth=1.5, label=f'Median: {median_val:.2f}')
        
        plt.title(f"Histogram: {os.path.basename(filepath)}\n{title_suffix}")
        plt.xlabel("Pixel Intensity")
        plt.ylabel("Frequency")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

    except Exception as e:
        print(f"❌ Error calculating histogram: {e}")

def plot_full_spectral_histogram(filepath, mode='overlay', bins=100, log_scale=False):
    """
    Plots the histogram for the ENTIRE multispectral image.
    
    Parameters:
    - filepath (str): Path to the 10-band spectral TIFF.
    - mode (str): 
        'overlay' = Plots 10 separate lines (one per band) on the same graph.
        'global'  = Aggregates all pixels into one single histogram.
    - bins (int): Number of bins.
    - log_scale (bool): Logarithmic Y-axis.
    """
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    try:
        img_data = tiff.imread(filepath)
        plt.figure(figsize=(12, 7))
        title_mode = ""
        
        # --- CASE 1: SPECTRAL CUBE (Both Internal & External) ---
        if img_data.ndim == 3:
            is_external = img_data.shape[2] > 1 and img_data.shape[2] > img_data.shape[0]
            num_bands = img_data.shape[2] if is_external else img_data.shape[0]
            
            if mode == 'overlay':
                print(f"📊 Plotting overlay of {num_bands} spectral bands...")
                cmap = plt.get_cmap('tab20')
                for i in range(num_bands):
                    wl = SILIOS_WAVELENGTHS.get(i, f"Band {i}")
                    band_pixels = img_data[:, :, i].flatten() if is_external else img_data[i].flatten()
                    
                    plt.hist(band_pixels, bins=bins, histtype='step', linewidth=1.5,
                             label=f"{wl}", color=cmap(i % 20), log=log_scale)
                
                # Limiter la légende si le nombre de bandes est immense (ex: 125)
                if num_bands <= 20:
                    plt.legend(loc='upper right', fontsize='small', ncol=2)
                title_mode = "Per-Band Analysis (Processed Cube)"
                
            else:
                print("📊 Plotting global distribution (3D Cube)...")
                plt.hist(img_data.flatten(), bins=bins, color='gray', alpha=0.8, log=log_scale, label="All Bands")
                title_mode = "Global Distribution (Processed Cube)"

        # --- CASE 2: RAW MOSAIC or THERMAL (2D) ---
        elif img_data.ndim == 2:
            print("📊 Plotting Global Raw Histogram.")
            plt.hist(img_data.flatten(), bins=bins, color='black', alpha=0.7, log=log_scale, label="Raw Pixels")
            max_val = np.max(img_data)
            plt.axvline(max_val, color='red', linestyle='--', label=f'Max Detected: {max_val}')
            title_mode = "Raw Sensor Distribution (Global)"
            plt.legend()
        else:
            print(f"❌ Error: Unrecognized image shape {img_data.shape}")
            return

        plt.title(f"{title_mode}\n{os.path.basename(filepath)}")
        plt.xlabel("Pixel Intensity")
        plt.ylabel("Frequency (Log)" if log_scale else "Frequency")
        plt.grid(True, alpha=0.3)
        plt.show()

    except Exception as e:
        print(f"❌ Error calculating histogram: {e}")

def plot_spectral_profile(filepath, smooth=True):
    """
    Plots the Spectral Signature with optional smoothing (Interpolation).
    
    Parameters:
    - filepath: Path to image
    - smooth: If True, draws a curved line. If False, draws straight lines.
    """
    
   
    if not os.path.exists(filepath):
        return

    try:
        img_data = tiff.imread(filepath)
        y_real = []
        x_real = []
        
        is_125_bands = (img_data.ndim == 3 and img_data.shape[2] == 125)
        is_external = img_data.ndim == 3 and img_data.shape[2] > 1 and img_data.shape[2] > img_data.shape[0]
        num_bands = img_data.shape[2] if is_external else (img_data.shape[0] if img_data.ndim == 3 else 10)

        # 1. Extraction des intensités (Y) et calcul des longueurs d'onde (X)
        for i in range(num_bands):
            if is_external:
                y_real.append(np.mean(img_data[:, :, i]))
            elif img_data.ndim == 3:
                y_real.append(np.mean(img_data[i]))
            else: # Raw mosaic 2D
                r_off, c_off = i // 4, i % 4
                y_real.append(np.mean(img_data[r_off::4, c_off::4]))
            
            # Calcul de l'axe X
            if is_125_bands:
                x_real.append(450 + i * (500 / 124))
            else:
                wl_str = SILIOS_WAVELENGTHS.get(i, str(400 + i*5)).replace("nm", "")
                x_real.append(float(wl_str))

        y_real = np.array(y_real)
        x_real = np.array(x_real)

        # 2. Lissage (Smoothing)
        x_smooth, y_smooth = x_real, y_real
        if smooth and len(x_real) > 3:
            x_smooth = np.linspace(x_real.min(), x_real.max(), 300)
            from scipy.interpolate import make_interp_spline
            spline = make_interp_spline(x_real, y_real, k=3) 
            y_smooth = spline(x_smooth)

        # 3. Affichage
        plt.figure(figsize=(10, 6))
        plt.plot(x_smooth, y_smooth, color='teal', linewidth=2.5, label='Interpolated Profile')
        # Pour 125 points, on réduit la taille des marqueurs pour que ce soit lisible
        marker_size = 15 if is_125_bands else 50
        plt.scatter(x_real, y_real, color='red', s=marker_size, zorder=5, label='Measured Bands')
        
        plt.title(f"Spectral Signature\n{os.path.basename(filepath)}")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Mean Intensity")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.show()

    except Exception as e:
        print(f"❌ Error: {e}")

def show_hyperspectral_image(donnees):
    """ Displays only the segmented RGB image. """
    if donnees is None: return
    
    plt.figure(figsize=(8, 8))
    plt.imshow(donnees["rgb"])
    plt.title("Segmented plant (Darkened background)")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def show_hyperspectral_graph(donnees):
    """Displays only the reflectance curve and the markers."""
    if donnees is None: return
    
    plt.figure(figsize=(10, 6))
    
    # Récupération des données du dictionnaire
    wl = donnees["wavelengths"]
    mean = donnees["mean"]
    std = donnees["std"]
    
    # Les repères verticaux
    reperes = {
        480: ['blue', 'Blue (480nm)'],
        550: ['green', 'Green (550nm)'],
        650: ['red', 'Red (650nm)'],
        740: ['orange', 'Red Edge (740nm)'],
        833: ['purple', 'NIR (833nm)']
    }

    for x_val, (couleur, nom) in reperes.items():
        if np.min(wl) <= x_val <= np.max(wl):
            plt.axvline(x=x_val, color=couleur, linestyle='--', linewidth=1.5, alpha=0.8, label=nom)

    # Tracé de la courbe et de l'écart-type
    plt.plot(wl, mean, color='black', linewidth=2.5, label='Mean', zorder=5)
    plt.fill_between(wl, np.maximum(0, mean - std), mean + std, color='gray', alpha=0.3, label='Variability', zorder=4)
    
    plt.title("Average Spectral Profile of the Plant")
    plt.xlabel(donnees["xlabel"])
    plt.ylabel("Reflectance (0 to 1)")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    plt.show()

def show_multiple_hyperspectral_graphs(liste_donnees, labels=None, afficher_std=True):
    """
    Affiche plusieurs courbes de réflectance sur le même graphique.
    
    Paramètres :
    - liste_donnees : Une liste contenant vos dictionnaires (ex: [set_haut, set_bas])
    - labels : (Optionnel) Une liste de noms pour la légende (ex: ["Plante Haut", "Plante Bas"])
    - afficher_std : (Optionnel) True pour montrer la variabilité, False pour alléger le graphique
    """
    # Nettoyage de la liste (on enlève les potentiels 'None' si une séparation a échoué)
    donnees_valides = [d for d in liste_donnees if d is not None]
    
    if not donnees_valides:
        print("⚠️ No valid data to show")
        return

    plt.figure(figsize=(12, 7))
    
    # 1. Tracé des repères verticaux (On le fait une seule fois en utilisant le premier set)
    wl_ref = donnees_valides[0]["wavelengths"]
    reperes = {
        480: ['blue', 'Bleu (480nm)'],
        550: ['green', 'Vert (550nm)'],
        650: ['red', 'Rouge (650nm)'],
        740: ['orange', 'Red Edge (740nm)'],
        833: ['purple', 'NIR (833nm)']
    }

    for x_val, (couleur, nom) in reperes.items():
        if np.min(wl_ref) <= x_val <= np.max(wl_ref):
            # zorder=1 met ces lignes tout au fond du graphique
            plt.axvline(x=x_val, color=couleur, linestyle='--', linewidth=1.5, alpha=0.5, label=nom, zorder=1)

    # 2. Palette de couleurs robustes pour bien distinguer les courbes
    couleurs_courbes = ['black', '#1f77b4', '#d62728', '#9467bd', '#8c564b', '#e377c2']

    # 3. Boucle sur toutes les données envoyées
    for i, donnees in enumerate(donnees_valides):
        wl = donnees["wavelengths"]
        mean = donnees["mean"]
        std = donnees["std"]
        
        # Définition du nom dans la légende
        nom_label = labels[i] if labels and i < len(labels) else f"Plante {i+1}"
        couleur_actuelle = couleurs_courbes[i % len(couleurs_courbes)]

        # Tracé de la moyenne
        plt.plot(wl, mean, color=couleur_actuelle, linewidth=2.5, label=nom_label, zorder=5)
        
        # Tracé de l'écart-type (plus transparent qu'avant pour supporter la superposition)
        if afficher_std:
            plt.fill_between(wl, np.maximum(0, mean - std), mean + std, 
                             color=couleur_actuelle, alpha=0.15, zorder=4)

    # 4. Mise en forme finale
    plt.title("Spectral Profile Comparison")
    plt.xlabel(donnees_valides[0]["xlabel"])
    plt.ylabel("Reflectance (0 to 1)")
    
    # Organiser la légende pour ne pas cacher les données
    plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), title="Legend", borderaxespad=0.)
    plt.grid(True, linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    plt.show()

def compare_plants_indices(liste_donnees, labels=None):
    """
    Calcule tous les indices spectraux pour une liste de plantes 
    et renvoie un tableau comparatif (Pandas DataFrame).
    """
    # On filtre les données non valides (ex: si une séparation a échoué)
    donnees_valides = [d for d in liste_donnees if d is not None]
    
    if not donnees_valides:
        print("⚠️ No data available.")
        return None

    # Dictionnaire qui va stocker les colonnes de notre tableau
    resultats = {}

    for i, donnees in enumerate(donnees_valides):
        # Définition du nom de la colonne (Plante 1, Plante 2, ou le nom personnalisé)
        nom_colonne = labels[i] if labels and i < len(labels) else f"Plante {i+1}"
        
        # On calcule tous les indices en gérant le cas où une plante est vide (masque vide)
        try:
            # Assurez-vous d'avoir bien importé/défini toutes vos fonctions de calcul avant !
            indices = {
                "NDVI (800/670)": calculate_mean_ndvi(donnees, cible_nir=800, cible_red=670),
                "GNDVI": calculate_mean_gndvi(donnees),
                "RVI": calculate_mean_rvi(donnees),
                "WI": calculate_mean_wi(donnees),
                "NDWI": calculate_mean_ndwi(donnees),
                "SIPI": calculate_mean_sipi(donnees),
                "PRI": calculate_mean_pri(donnees),
                "ARI": calculate_mean_ari(donnees),
                "CARI": calculate_mean_cari(donnees)
            }
        except NameError as e:
            print(f"❌ Erreur : L'une de vos fonctions de calcul est manquante ({e})")
            return None

        # On ajoute les résultats de cette plante dans notre dictionnaire global
        resultats[nom_colonne] = indices

    # ---------------------------------------------------------
    # Création et formatage du tableau Pandas
    # ---------------------------------------------------------
    df = pd.DataFrame(resultats)
    
    # On arrondit tout à 5 décimales pour que ce soit propre
    df = df.round(5)
    
    # On ajoute un nom à la colonne des indices
    df.index.name = "Health Indices"
    
    return df

def explain_spectral_index(index_name="ALL"):
    """
    Helper function to explain Vegetative/Spectral Indices (VIs) with disease intervals.
    """
    
    indices_db = {
        "NDVI": {
            "name": "Normalized Difference Vegetation Index",
            "formula": "(R800 - R670) / (R800 + R670)",
            "purpose": "Estimates vegetation coverage based on chlorophyll content.",
            "values": {
                "Healthy Wheat": "0.75 to 0.90",
                "Yellow Rust": "0.40 to 0.65 (Chlorosis reduces NIR reflection & increases Red reflection)",
                "Septoria (STB)": "0.30 to 0.60 (Severe necrosis destroys chlorophyll rapidly)"
            }
        },
        "GNDVI": {
            "name": "Green Normalized Difference Vegetation Index",
            "formula": "(NIR - GREEN) / (NIR + GREEN)",
            "purpose": "Measures nitrogen content and identifies withered crops.",
            "values": {
                "Healthy Wheat": "0.65 to 0.85",
                "Diseased (General)": "< 0.50 (More sensitive to early chlorophyll loss than NDVI)"
            }
        },
        "RVI": {
            "name": "Ratio Vegetation Index",
            "formula": "R800 / R670",
            "purpose": "Estimates plant biomass.",
            "values": {
                "Healthy Wheat": "4.0 to 8.0+",
                "Yellow Rust / STB": "1.5 to 3.0 (Correlates strongly with loss of green biomass)"
            }
        },
        "WI": {
            "name": "Water Index",
            "formula": "R900 / R970",
            "purpose": "Evaluates water stress in plants.",
            "values": {
                "Healthy Wheat": "0.95 to 1.05",
                "Septoria (STB)": "Drops < 0.90 (STB causes rapid water loss in necrotic lesions)"
            }
       },
        "NDWI": {
            "name": "Normalized Difference Water Index",
            "formula": "(Gao, 1996) usually (NIR - SWIR) / (NIR + SWIR)",
            "purpose": "Evaluates leaf water content, crucial for STB.",
            "values": {
                "Healthy Wheat": "0.20 to 0.40",
                "Septoria (STB)": "-0.10 to 0.10 (Strong indicator of tissue drying from STB)"
            }
        },
        "SIPI": {
            "name": "Structure Insensitive Pigment Index",
            "formula": "(R800 - R445) / (R800 - R680)",
            "purpose": "Estimates the ratio of carotenoids to chlorophyll.",
            "values": {
                "Healthy Wheat": "0.80 to 0.95",
                "Yellow Rust": "1.0 to 1.2+ (Increases as chlorophyll degrades but carotenoids remain)"
            }
        },
        "PRI": {
            "name": "Photochemical Reflectance Index",
            "formula": "(R531 - R570) / (R531 + R570)",
            "purpose": "Related to photosynthesis efficiency. Excellent for early rust detection.",
            "values": {
                "Healthy Wheat": "0.02 to 0.08 (Positive values indicate healthy photosynthesis)",
                "Yellow Rust": "-0.15 to -0.05 (Drops significantly even *before* pustules are visible)"
            }
        },
        "ARI": {
            "name": "Anthocyanin Reflectance Index",
            "formula": "(1 / R510) - (1 / R700)",
            "purpose": "Determines anthocyanin content (stress response).",
            "values": {
                "Healthy Wheat": "Very low (close to 0)",
                "Stressed/Diseased": "Increases significantly as the plant produces protective pigments"
            }
        },
            "CARI": {
            "name": "Carotenoid Reflectance Index",
            "formula": "(1 / R510) - (1 / R550)",
            "purpose": "Estimates the carotenoid content in plants.",
            "values": {
                "Healthy Wheat": "Low baseline",
                "Yellow Rust": "Spikes heavily (Yellow rust spores/pustules are rich in carotenoid-like compounds)"
            }
        }
    }
    
    index_name = index_name.upper().strip()
    
    if index_name == "ALL":
        print(f"{'--- VEGETATIVE & SPECTRAL INDICES ---':^70}")
        for key, data in indices_db.items():
            print(f"\n[{key}] - {data['name']}")
            print(f"  Formula : {data['formula']}")
            print(f"  Purpose : {data['purpose']}")
            print("  Typical Values:")
            for condition, val in data['values'].items():
                print(f"    - {condition}: {val}")
        print("\n" + "-"*70)
        
    elif index_name in indices_db:
        data = indices_db[index_name]
        print(f"[{index_name}] - {data['name']}")
        print(f"➔ Formula : {data['formula']}")
        print(f"➔ Purpose : {data['purpose']}")
        print("➔ Typical Values:")
        for condition, val in data['values'].items():
            print(f"    • {condition}: {val}")
    else:
        print(f"❌ Index '{index_name}' not found. Available: {', '.join(indices_db.keys())}")


def calculate_mean_ndvi(donnees, cible_nir=800, cible_red=670):
    """
    Calcule le NDVI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_nir = np.argmin(np.abs(wavelengths - cible_nir))
    band_red = np.argmin(np.abs(wavelengths - cible_red))
    
    print(f"📊 Calcul NDVI ({cible_nir}/{cible_red}) -> Bandes utilisées : {band_nir} et {band_red}")
    
    # 3. Extraire les pixels de la plante
    pixels_nir = cube[:, :, band_nir][masque]
    pixels_red = cube[:, :, band_red][masque]
    
    if len(pixels_nir) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    ndvi_array = (pixels_nir - pixels_red) / (pixels_nir + pixels_red + 1e-6)
    
    return float(np.mean(ndvi_array))





    

def calculate_mean_gndvi(donnees, cible_nir=800, cible_green=550):
    """
    Calcule le GNDVI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_nir = np.argmin(np.abs(wavelengths - cible_nir))
    band_green = np.argmin(np.abs(wavelengths - cible_green))
    
    print(f"📊 Calcul GNDVI ({cible_nir}/{cible_green}) -> Bandes utilisées : {band_nir} et {band_green}")
    
    # 3. Extraire les pixels de la plante
    pixels_nir = cube[:, :, band_nir][masque]
    pixels_green = cube[:, :, band_green][masque]
    
    if len(pixels_nir) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    gndvi_array = (pixels_nir - pixels_green) / (pixels_nir + pixels_green + 1e-6)
    
    return float(np.mean(gndvi_array))





    
def calculate_mean_rvi(donnees, cible_nir=800, cible_red=670):
    """
    Calcule le RVI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_nir = np.argmin(np.abs(wavelengths - cible_nir))
    band_red = np.argmin(np.abs(wavelengths - cible_red))
    
    print(f"📊 Calcul RVI ({cible_nir}/{cible_red}) -> Bandes utilisées : {band_nir} et {band_red}")
    
    # 3. Extraire les pixels de la plante
    pixels_nir = cube[:, :, band_nir][masque]
    pixels_red = cube[:, :, band_red][masque]
    
    if len(pixels_nir) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    rvi_array = (np.mean(pixels_nir)) / (np.mean(pixels_red) + 1e-6)
    
    return float(rvi_array)



    
def calculate_mean_wi(donnees, cible_nir1=900, cible_nir2=970):
    """
    Calcule le WI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_nir1 = np.argmin(np.abs(wavelengths - cible_nir1))
    band_nir2 = np.argmin(np.abs(wavelengths - cible_nir2))
    
    print(f"📊 Calcul WI ({cible_nir1}/{cible_nir2}) -> Bandes utilisées : {band_nir1} et {band_nir2}")
    
    # 3. Extraire les pixels de la plante
    pixels_nir1 = cube[:, :, band_nir1][masque]
    pixels_nir2 = cube[:, :, band_nir2][masque]
    
    if len(pixels_nir1) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    wi_array = (np.mean(pixels_nir1)) / (np.mean(pixels_nir2) + 1e-6)
    
    return float(wi_array)



    
def calculate_mean_ndwi(donnees, cible_nir1=900, cible_nir2=970):
    """
    Calcule le NDWI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_nir1 = np.argmin(np.abs(wavelengths - cible_nir1))
    band_nir2 = np.argmin(np.abs(wavelengths - cible_nir2))
    
    print(f"📊 Calcul NDWI ({cible_nir1}/{cible_nir2}) -> Bandes utilisées : {band_nir1} et {band_nir2}")
    
    # 3. Extraire les pixels de la plante
    pixels_nir1 = cube[:, :, band_nir1][masque]
    pixels_nir2 = cube[:, :, band_nir2][masque]
    
    if len(pixels_nir1) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    ndwi_array = (pixels_nir1 - pixels_nir2) / (pixels_nir1 + pixels_nir2 + 1e-6)
    
    return float(np.mean(ndwi_array))


    
    
def calculate_mean_sipi(donnees, cible_blue=445, cible_red=680, cible_nir=800):
    """
    Calcule le SIPI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_blue = np.argmin(np.abs(wavelengths - cible_blue))
    band_red = np.argmin(np.abs(wavelengths - cible_red))
    band_nir = np.argmin(np.abs(wavelengths - cible_nir))
    
    
    print(f"📊 Calcul SIPI ({cible_blue}/{cible_red}/{cible_nir}) -> Bandes utilisées : {band_blue}, {band_red} et {band_nir}")
    
    # 3. Extraire les pixels de la plante
    pixels_nir = cube[:, :, band_nir][masque]
    pixels_red = cube[:, :, band_red][masque]
    pixels_blue = cube[:, :, band_blue][masque]
    
    if len(pixels_nir) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    sipi_array = (np.mean(pixels_nir) - np.mean(pixels_blue)) / (np.mean(pixels_nir) - np.mean(pixels_red) + 1e-6)
    
    return float(sipi_array)

def calculate_mean_pri(donnees, cible_red1=531, cible_red2=570):
    """
    Calcule le PRI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_red1 = np.argmin(np.abs(wavelengths - cible_red1))
    band_red2 = np.argmin(np.abs(wavelengths - cible_red2))
    
    
    print(f"📊 Calcul PRI ({cible_red1}/{cible_red2}/) -> Bandes utilisées : {band_red1} et {band_red2}")
    
    # 3. Extraire les pixels de la plante
    pixels_red1 = cube[:, :, band_red1][masque]
    pixels_red2 = cube[:, :, band_red2][masque]
    
    if len(pixels_red1) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    pri_array = (pixels_red2 - pixels_red1) / (pixels_red2 + pixels_red1 + 1e-6)
    
    return float(np.mean(pri_array))
def calculate_mean_ari(donnees, cible_red=510, cible_nir=700):
    """
    Calcule le ARI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_red = np.argmin(np.abs(wavelengths - cible_red))
    band_nir = np.argmin(np.abs(wavelengths - cible_nir))
    
    
    print(f"📊 Calcul ARI ({cible_red}/{cible_nir}/) -> Bandes utilisées : {band_red} et {band_nir}")
    
    # 3. Extraire les pixels de la plante
    pixels_red = cube[:, :, band_red][masque]
    pixels_nir = cube[:, :, band_nir][masque]
    
    if len(pixels_nir) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    ari_array = (1 / (np.mean(pixels_red) + 1e-6)) - 1 / (np.mean(pixels_nir) + 1e-6)
    
    return float(ari_array)

def calculate_mean_cari(donnees, cible_red=510, cible_nir=550):
    """
    Calcule le CARI moyen d'une plante en utilisant directement 
    le dictionnaire généré par le moteur de préparation.
    """
    # Sécurité au cas où le moteur aurait échoué
    if donnees is None:
        print("⚠️ No data found")
        return None
        
    # 1. Extraction automatique depuis le dictionnaire
    cube = donnees["cube"]
    wavelengths = donnees["wavelengths"]
    masque = donnees["masque"]
    
    # 2. Trouver l'indice de la bande la plus proche
    band_red = np.argmin(np.abs(wavelengths - cible_red))
    band_nir = np.argmin(np.abs(wavelengths - cible_nir))
    
    
    print(f"📊 Calcul ARI ({cible_red}/{cible_nir}/) -> Bandes utilisées : {band_red} et {band_nir}")
    
    # 3. Extraire les pixels de la plante
    pixels_red = cube[:, :, band_red][masque]
    pixels_nir = cube[:, :, band_nir][masque]
    
    if len(pixels_red) == 0:
        print("⚠️ The mask is empty, no pixel to analyse")
        return None
        
    # 4. Calcul et Moyenne
    ari_array = (1 / (pixels_red + 1e-6)) - 1 / (pixels_nir + 1e-6)
    
    return float(np.mean(ari_array))