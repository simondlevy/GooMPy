# GooMPy
Google Maps for Python

GooMPy provide a Python interface tot the Google Static Maps API, automaticallyd ownloading and stitching together map tiles into a single image that you can zoom and pan.  Because Google limits the number of tiles that you can download during a given time period, we recommend setting up an API key as described here:
  
  https://developers.google.com/maps/documentation/staticmaps/#api_key
  
Once you have your key, put it in the file goompy/key.py, and GooMPy will use it in fetching map tiles.
