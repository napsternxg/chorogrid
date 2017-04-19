import requests
import pandas as pd
from bs4 import BeautifulSoup
from scipy.stats import binned_statistic
#from locationfinder import LocationFinder


# get details from Bolstad
url = "http://www.erikbolstad.no/geo/skandinavia/norske-kommunesenter/txt/"
r = requests.get(url)
df = pd.read_html(r.text)[0]
df = df.sort_values(by="Fylkenummer",ascending=False)



kommuner = {}
for line in df.iterrows():
    #print(len(line), type(line)) #print(line[1][0])
    #print()
    kommuner[int(line[1][0])] = {
        'navn': line[1][3],
        'geoname_id': line[1][2],
        'Fylkenummer': line[1][4],
        'Folketal': line[1][6],
        'lat': line[1][12],
        'long': line[1][13]
    }

# # sorted(alternatives, key=lambda x: (x[6], x[4]))
# for k, v in kommuner.items():
#     print(k,v)
#
# #kommune[101].update(ny)




# grab paths from wikipedia svg
from svgpathtools import svg2paths
paths, attributes = svg2paths('Norway_municipalities_2012_blankSandefix.svg')
table = []
for k in range(len(attributes)):
    # fuck, they keep merging municipalities...
    if int(attributes[k]['id']) == 706: # sandefjord is merged
        komid = 710 # bolstads nr for sandefjord
    elif int(attributes[k]['id']) == 719: # andebu er slått sammen
        komid = 710 # sandefjord = stokke + andebu + sandefjord
    elif int(attributes[k]['id']) == 1901: # hardstad..
        komid = 1903
    elif int(attributes[k]['id']) == 1915: # Bjarøy..
        komid = 1903 # er nå Hardstd
    else:
        komid = int(attributes[k]['id'])

    #print(attributes[k]['inkscape:label'])
    #print(kommuner[komid])
    #print()
    row = [komid, attributes[k]['inkscape:label'], str(attributes[k]['d']), kommuner[komid]['Fylkenummer'], kommuner[komid]['lat'], kommuner[komid]['long'], kommuner[komid]['geoname_id'], kommuner[komid]['Folketal']]
    table.append(row)

df = pd.DataFrame(table)
df.columns = ["kommuneid", "Navn", "map_path", "fylkesnummer", "lat", "long", "geoname_id", "folketal"]
df["square_x"] = ""
df["square_y"] = ""
print(df.head())
print(df.tail())


# lage grid
def create_grid_with_bins(n_heigth=40, n_width=30):
    # make coordinates negative so 0.0 is top left
    df["neg_lat"] = -df["lat"]
    #df["neg_long"] = -df["long"]


    lat_bin_nr = binned_statistic(df['neg_lat'], df['neg_lat'], statistic='count', bins=n_heigth, range=None).binnumber
    lon_bin_nr = binned_statistic(df['long'], df['long'], statistic='count', bins=n_width, range=None).binnumber

    for n,la,lo in zip(df["kommuneid"].values,lat_bin_nr, lon_bin_nr):
        #print(la-1,lo-1, n)
        df.loc[df.kommuneid == n, "square_y"] = la-1
        df.loc[df.kommuneid == n, "square_x"] = lo-1

def compact_grid():
    df2 = df[["kommuneid", "Navn", "fylkesnummer","lat","long"]]
    df2 = df2.sort_values(by="fylkesnummer",ascending=False)
    # Grupper på fylke, lag liste av kommuner pr fylke
    fylk = {}
    fylke_liste = []
    for row in df.iterrows():
        if row[1]['fylkesnummer'] not in fylk.keys():
            fylk[row[1]['fylkesnummer']] = []
        fylk[row[1]['fylkesnummer']].append(row[1].tolist())

    line = 0
    pos = 0
    for i in sorted(fylk.keys(), reverse=True):
        fylk[i].sort(key=lambda x: x[4]) # sort from west to east?
        for ko in fylk[i]:
            pos +=1
            # insert (line,pos-1) in df in square cols
            df.loc[df.kommuneid == ko[0], "square_y"] = line
            df.loc[df.kommuneid == ko[0], "square_x"] = pos
            #print(ko[0],(line,pos-1),"\t", end="")
            if pos == 20: # antall pr linje
                pos = 0
                line += 1



def nice_grid():
    """This is getting x&y by reading a .svg that I have manually arranged into
    the chape on norway. Did not find the elegant way to do this..."""
    # norge er 52 rader høyt (y) og 43 bredt (x), men føkk det, rutene er 10px
    HEIGTH = 10# 52
    WIDTH = 10 #43

    # df_grid = pd.DataFrame(columns=["id", "x", "y"])

    import lxml.etree as ET

    _file = 'grid5_plain_final.svg'
    for event, elem in ET.iterparse(_file):

        if elem.tag == "{http://www.w3.org/2000/svg}rect":
            #print(event, elem.tag, elem.text)
            for name, value in elem.items():
                if name in ["id", "x", "y"]:
                    if name=="id":
                        #print("Kommune", value.replace("rect", ""), end=" - ")
                        kom = int(value.replace("rect", ""))
                    elif name == "x":
                        #print(name, round(float(value), 0), end=" ")
                        x = round(float(value) / WIDTH, 0)
                    else:
                        y = round(float(value) / HEIGTH, 0)

            df.loc[df.kommuneid == kom, "square_y"] = y
            df.loc[df.kommuneid == kom, "square_x"] = x
            # df_grid = df_grid.append({
            #          "id": kom,
            #          "x":  x,
            #          "y": y
            #           }, ignore_index=True)

#compact_grid()
#create_grid_with_bins(n_heigth=80, n_width=70)
nice_grid()


print(df.head())
print(df.tail())

# import sys
# sys.exit()
df.to_csv("../chorogrid/databases/norway_municilalities.csv")
print("saved")
