import pandas as pd
import requests
import re
from time import sleep

#Change YOUR_API_KEY and YOUR_FILE_NAME 

# https://maps.nyc.gov/geoclient/v1/doc
# Get the API here https://api-portal.nyc.gov/api-details#api=geoclient&operation=geoclient
API_KEY = 'YOUR_API_KEY'

def geocode_intersection(boro1, street1, street2, compass=None):
    headers = {
        'Ocp-Apim-Subscription-Key': API_KEY
    }
    url = f'https://api.nyc.gov/geo/geoclient/v1/intersection.json?crossStreetOne={street1}&crossStreetTwo={street2}&borough={boro1}'
    
    r = requests.get(url, headers=headers)
    sleep(0.01)
    return r.json()

df = pd.read_csv('YOUR_FILE_NAME')

def getStreets(text):
    # Try splitting using AT, 'and', and '(0-9) AT (direction)'
    streets_list = re.split(r" and | AT | \d+ FT (N|S|W|E) ", text)
    if len(streets_list) == 3:
        # If the length is exactly 3, return a pandas Series with the three elements
        return pd.Series(streets_list)
    elif len(streets_list) > 3:
        # If the length is greater than 3, take the first three elements, discard the rest
        streets_list = streets_list[:3]
        return pd.Series(streets_list)
    else:
        return pd.Series([text, ''])

df[["Street1", "sep", "Street2"]] = df["Intersection"].apply(getStreets)

def getLatLng(row):
    json = geocode_intersection(row['Violation County'], row['Street1'], row['Street2'])
    d = json['intersection']
    try:
        return pd.Series([d['longitude'], d['latitude']])
    except:
        if row['sep'] and 'STREETS INTERSECT TWICE' in d['message'] and row['sep'] in ('N', 'S', 'W', 'E'): 
            # This can probably be fixed if we have a compass direction
            try: 
                json = geocode_intersection(row['Borough'], row['Street1'], row['Street2'], row['sep'])
                d = json['intersection']
                return pd.Series([d['longitude'], d['latitude']])
            except:
                return pd.Series([None, None])
        else:
            return pd.Series([None, None])

df[['longitude', 'latitude']] = df.apply(getLatLng, axis=1)
df.plot.scatter(x='longitude', y='latitude')

# Manual geocode those who didn't work
df[pd.isna(df['longitude'])]
df.to_csv('intersections_geocoded.csv', index=False)