import numpy as np  # type: ignore
import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
from streamlit_drawable_canvas import st_canvas  # type: ignore
from PIL import Image  # type: ignore
import datetime
import sunpy.visualization.colormaps as cm  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from urllib.request import urlopen, Request
import json
import re
import yaml  # type: ignore
from pathlib import Path

# =========================================================
# -------------------- CONFIGURATION ----------------------
# =========================================================

with open('Config\\config_project.yaml', 'r') as file:
    config = yaml.safe_load(file)

with open('Config\\config_documentation.yaml', 'r') as file:
    documentation = yaml.safe_load(file)

cmap_aia = plt.get_cmap("sdoaia304")  # type: ignore
cmap_grey = plt.get_cmap("Greys")  # type: ignore
st.set_page_config(layout="wide")

# =========================================================
# -------------------- FUNCTIONS --------------------------
# =========================================================

# --------- FUNCTIONS TO DISPLAY MEDIA --------------------

def get_norm_canvas_image_linear(z, vmin, vmax, cmap=cmap_aia):
    flipped_z = np.flipud(z)
    # Clip + normalize based on sliders
    z_clipped = np.clip(flipped_z, vmin, vmax)
    z_norm = (z_clipped - vmin) / (vmax - vmin)
    # color map
    rgba = cmap(z_norm)   # shape: (ny, nx, 4)
    # Convert to image
    rgb = (rgba[:, :, :3] * 255).astype(np.uint8)  # drop alpha
    # Create image
    image = Image.fromarray(rgb)
    return image


def display_documentation_image(documentation, key):
    try:
        img_cfg = documentation["documentation_media"]["media_files"][key]
        base_path = documentation["documentation_media"]["url"]
        img_path = Path(base_path) / img_cfg["filename"]
        if not img_path.exists():
            st.warning(f"Image not found: {img_path}")
            return
        st.image(
            str(img_path),
            width=img_cfg.get("width"),
            caption=img_cfg.get("caption")
        )
    except KeyError:
        st.error(f"Missing config for image key: {key}")

def draw_time_arrow(width="700px", label="Time"):
    html = f"""
    <div style="width: 100%; text-align: left; margin-top: 5px;">
        <div style="position: relative; width: {width}; height: 20px;">
            <div style="
                position: absolute;
                top: 50%;
                left: 0%;
                right: 0%;
                height: 2px;
                background-color: black;">
            </div>
            <div style="
                position: absolute;
                right: 0%;
                top: 50%;
                transform: translateY(-50%);
                font-size: 20px;">
                ➤
            </div>
        </div>
        <div style="margin-top: 1px;">
            {label}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# --------- FUNCTIONS TO GET DATA ----------------------

@st.cache_data
def get_all_subjects(config):
    all_subjects = []
    page = 1
    template = config["project_urls"]["zooniverse_subjects"]
    subject_set_id = config["zooniverse_config"]["subject_set_id"]
    while True:
        url = template.format(subject_set_id=subject_set_id, page=page)
        headers = {'Accept': 'application/vnd.api+json; version=1'}
        request = Request(url, headers=headers)
        response = urlopen(request).read()
        data = json.loads(response)
        subjects = data.get("subjects", [])
        if not subjects:
            break
        all_subjects.extend(subjects)
        page += 1
    return all_subjects

@st.cache_data
def get_subject_metadata(subject_id):
    url = f"https://www.zooniverse.org/api/subjects/{subject_id}"
    headers = {
        'Accept': 'application/vnd.api+json; version=1',
        'Content-Type': 'application/json'
    }
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    data = json.loads(response)
    # Extract metadata
    subject = data["subjects"][0]
    metadata = subject["metadata"]
    return metadata

def get_time_array_from_metadata(metadata):
    raw = metadata['time_data']
    times = np.array([datetime.datetime.fromisoformat(t) for t in json.loads(raw)])
    return times

def get_float_array_from_metadata(metadata, key='distance_data'):
    raw = metadata[key]
    array = np.array(json.loads(raw))
    return array

def get_td_data_from_metadata(metadata):
    time = get_time_array_from_metadata(metadata)
    distance = get_float_array_from_metadata(metadata, key='distance_data')
    time_dist = get_float_array_from_metadata(metadata, key='time_distance_data')
    run_diff = get_float_array_from_metadata(metadata, key='rundif_time_distance_data')
    return time, distance, time_dist, run_diff


# --------- FUNCTION TO MOVE TO THE NEXT JET ---------------

def next_jet(subject_index, subject_ids):
    if subject_index < len(subject_ids) - 1:
        st.session_state["subject_index"] += 1
    else:
        st.success("All jets completed!")
        st.stop()

    st.rerun()


# =========================================================
# -------------------- GET SUBJECTS -----------------------
# =========================================================

subjects = get_all_subjects(config)
subject_id_list = [s['id'] for s in subjects]


# =========================================================
# -------------------- SESSION STATE ----------------------
# =========================================================

if "scale" not in st.session_state:
    st.session_state.scale = "log"
if "runningdiff" not in st.session_state:
    st.session_state.runningdiff = "off"
if "username" not in st.session_state:
    st.session_state["username"] = "guest"
if "subject_ids" not in st.session_state:
    st.session_state["subject_ids"] = subject_id_list  # your list
if "subject_index" not in st.session_state:
    st.session_state["subject_index"] = 0

st.write(f"Logged in as: {st.session_state['username']}")


# =========================================================
# -------------------- LOGIN ------------------------------
# =========================================================

if st.session_state["username"] == "guest":
    if st.button("Zooniverse login"):
        pass
else:
    if st.button("Log out"):
        st.session_state["username"] = "guest"


# =========================================================
# ------------- LOAD DATA FOR CURRENT SUBJECT -------------
# =========================================================

# get current subject
subject_ids = st.session_state["subject_ids"]
subject_index = st.session_state["subject_index"]
current_subject_id = subject_ids[subject_index]

# get metadata
metadata = get_subject_metadata(current_subject_id)
time, distance, time_dist, run_diff_td = get_td_data_from_metadata(metadata)

# read jet id to access local context media (not part of the subject)
current_jet_id = metadata['jet_id']
jet_year = current_jet_id[4:8]
context_path = Path(config['project_urls']['context_media']+jet_year+'\\'+current_jet_id+'_304\\'+current_jet_id+'_304.mp4')

# =========================================================
# -------------------- UI CONTROLS ------------------------
# =========================================================

with st.sidebar:
    st.title('Image display controls')
    with st.expander("ℹ️ About the controls"):
        st.write(documentation['sidebar_text']['control_text'])
    
    left_side, right_side = st.columns([1,1])

    with left_side:
        rundiff = st.radio("Running difference", ["off", "on"])
        st.session_state.runningdiff = rundiff
    with right_side:
        scale = st.radio("Scale", ["log", "linear"])
        st.session_state.scale = scale


# =========================================================
# -------------------- IMAGE CREATION ---------------------
# =========================================================

# Data can be intensity of running difference
if st.session_state.runningdiff == "off":
    z = time_dist
    cmap = cmap_aia
else:
    z = run_diff_td
    cmap = cmap_grey
    st.session_state.scale = "linear"

# Convert datetime → numeric (seconds since start)
x_seconds = np.array([(xx - time[0]).total_seconds() for xx in time])
y = distance

# Choose data depending on scale (linear or log10)
z_safe = np.where(z > 0, z, np.nan)
if st.session_state.scale == "log":
    z_display = np.log10(z_safe)
else:
    z_display = z

# get the min and max values for display
z_min = float(np.nanmin(z_display))
z_max = float(np.nanmax(z_display))


# =========================================================
# ---------------- UI CONTROLS Continued ------------------
# =========================================================

# Sliders
with st.sidebar:
    vmin, vmax = st.slider(label='Levels', min_value=z_min, max_value=z_max, value=(z_min, z_max))


# =========================================================
# -------------------- MAIN BODY --------------------------
# =========================================================

# Get image
image = get_norm_canvas_image_linear(z_display, vmin, vmax, cmap=cmap)

# display title, help, context data
st.title("Time–Distance Line Drawing Tool")

main, right = st.columns([6, 3])

with main:
    st.write("Draw lines on the image, then click 'Save lines, get new subject' (on the side panel).")

    with st.expander("ℹ️ About this task"):
        st.write(documentation['main_text']['about_this_task']['intro_text'])

        if "show_info" not in st.session_state:
            st.session_state.show_info = False

        if st.button("See an example"):
            st.session_state.show_info = True

        if st.session_state.show_info:
            st.info(documentation['main_text']['about_this_task']['example_text1'])
            display_documentation_image(documentation, 'example_01')
            st.info(documentation['main_text']['about_this_task']['example_text2'])
            display_documentation_image(documentation, 'example_02')
            if st.button("Close"):
                st.session_state.show_info = False

with right:
    with st.container(border=True):
        st.write('#### More info about this jet')
        st.video(str(context_path))
        st.write('Play the video to see the jet developing in the associated box.')

        with st.expander("ℹ️ How do we produce the time-distance plot?"):
            st.write(documentation["right_col_text"]["how_do_we_produce_td"]["text1"])
            display_documentation_image(documentation, 'img_td_01')
            st.write(documentation["right_col_text"]["how_do_we_produce_td"]["text2"])
            display_documentation_image(documentation, 'img_td_02')
            st.write(documentation["right_col_text"]["how_do_we_produce_td"]["text3"])
            display_documentation_image(documentation, 'img_td_03')
            st.write(documentation["right_col_text"]["how_do_we_produce_td"]["text4"])
            display_documentation_image(documentation, 'img_td_04')
            st.write(documentation["right_col_text"]["how_do_we_produce_td"]["text5"])
            display_documentation_image(documentation, 'img_td_05')


# =========================================================
# -------------------- CANVAS -----------------------------
# =========================================================

with main:
    canvas_key = f"canvas_{st.session_state['subject_index']}"
    canvas = st_canvas(
        background_image=image,
        update_streamlit=True,
        height=400,  # height=image.height,
        width=700,  # width=image.width*2,
        drawing_mode="line",
        stroke_width=2,
        stroke_color="cyan",
        key=canvas_key,
    )
    # Draw arrow for time
    draw_time_arrow()

    # Add some documentation below the canvas
    st.write(" ")
    with st.expander("ℹ️ Why are we doing this?"):
        st.write(documentation["main_text"]["why_are_we_doing_this"]["text1"])
        

# =========================================================
# -------------------- COORDINATE MAPPING ------------------
# =========================================================

def pixel_to_data(px, py, x_seconds, y, width, height):
    # Map pixel → time (seconds)
    t_sec = x_seconds[0] + (px / width) * (x_seconds[-1] - x_seconds[0])
    # Convert back to datetime
    t = time[0] + datetime.timedelta(seconds=t_sec)
    # Map pixel → distance (invert y-axis)
    y_val = y[0] + ((height - py) / height) * (y[-1] - y[0])
    return t, y_val


# =========================================================
# -------------------- EXTRACT LINES -----------------------
# =========================================================

lines = []

# NEED TO ALSO SAVE THE NUMERIC VALUE OF X FOR AGGREGATION PURPOSE... 
# WE ALSO NEED TO STORE THE IMAGE WIDTH AND HEIGHT, AND MAYBE THE LIMITS OF X_SECONDS,
# TO EASY CONVERSION OF THE AGGREGATED VALUE LATER
if canvas.json_data is not None:
    objects = canvas.json_data["objects"]

    for obj in objects:
        if obj["type"] == "line":

            t0, y0 = pixel_to_data(
                obj["x1"], obj["y1"],
                x_seconds, y,
                image.width, image.height
            )

            t1, y1 = pixel_to_data(
                obj["x2"], obj["y2"],
                x_seconds, y,
                image.width, image.height
            )

            lines.append({
                "t0": str(t0),
                "y0": float(y0),
                "t1": str(t1),
                "y1": float(y1),
            })

# =========================================================
# -------------------- SAVE CLASSIFICATION ----------------
# =========================================================

with st.sidebar:
    st.title("When done drawing lines:")

    if st.button("Save lines, get new subject", use_container_width=True):
        if lines:
            # 1. Save your CSV
            df = pd.DataFrame(lines)
            df["username"] = st.session_state.get("username", "guest")
            df["subject_id"] = current_subject_id
            df.to_csv(f"output_{current_subject_id}.csv", index=False)
            st.success("Saved to lines.csv")

            next_jet(subject_index, subject_ids)
        else:
            st.warning("No line drawn. Please select one of the reasons below.")

    st.write("### If you do not see any ejection:")
    st.write("Play the video of the jet on the right to assess the situation, then pick one of the options below.")
    with st.expander("ℹ️ More information"):
        st.write(documentation["sidebar_text"]["no_ejection_info_text"]["text1"])
        st.info(documentation["sidebar_text"]["no_ejection_info_text"]["info1"])
        st.write(documentation["sidebar_text"]["no_ejection_info_text"]["text2"])
        st.info(documentation["sidebar_text"]["no_ejection_info_text"]["info2"])

    if st.button("No jet in context movie", use_container_width=True):
        next_jet(subject_index, subject_ids)
    if st.button("Jet too faint", use_container_width=True):
        next_jet(subject_index, subject_ids)
    if st.button("Jet not aligned with the box", use_container_width=True):
        next_jet(subject_index, subject_ids)
    if st.button("Something else", use_container_width=True):
        next_jet(subject_index, subject_ids)