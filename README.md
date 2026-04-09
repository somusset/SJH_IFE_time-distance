# SJH_IFE_time-distance
Solar Jet Hunter front end for the Zooniverse Incubator Front End workshop. This front end is to annotate time-distance plots of solar jets.

# Quick start

Check out this application at https://solarjethunter-velocity.streamlit.app/ 

The application will run locally. In a conda environment in which the Zooniverse panoptes client is installed, and streamlit is installed, the app can be run with:
```bash
streamlit run app4_time-distance.py
```

# Notes

## Subjects
This application will run with subjects that have both a png and a mp4 media.    
The manifest provides (in addition to the metadata) two rows called `png_file` and `mp4_file`. These fields are set as "locations" for each subject.

## Classifications
For the moment the classification contains the results of two tasks:
- T0 contains a list of lines
- T1 contains a string that relay one answer in the multi-choice question.

Note that if T0 is not empty, we expect T1 to be empty - and the reverse is true too.
