import os
os.chdir('/tmp')

path = '/climatempo/'

import geopandas
import geemap
import geojson
import contextily as cx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
from PyPDF2 import PdfFileWriter, PdfFileReader
import requests
from datetime import datetime
import ee
import json
service_account = 'XXXXXXXXXXXX@appspot.gserviceaccount.com '
credentials = ee.ServiceAccountCredentials(service_account, path + 'cropclass.json')
ee.Initialize(credentials)

def moeda(valor, unidade):
    r = "{0:,.2f}".format(valor)
    t = r.split('.')
    vl1 = t[0].replace(',','.')
    return vl1 + ',' + t[-1] + ' ' + unidade

def desenhaMapa(mapas):
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    fig, ax = plt.subplots(figsize=(20, 10))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.1)
    mapas.plot(ax=ax, alpha=1, column='ssm', legend=True, legend_kwds={'label': "Umidade do Solo (mm)", 'orientation': "horizontal"}, cax=cax)
    ax.margins(0.2)
    cx.add_basemap(ax, crs=mapas.crs, source=cx.providers.Esri.WorldImagery)
    #ax.legend(handles=legendas, loc='center left',bbox_to_anchor=(1, 0.5), prop={'size':30})
    ax.axis('off')
    plt.savefig('/tmp/figura.png',bbox_inches='tight')

def chuvas(mapas):
    import pandas as pd
    f = mapas.total_bounds
    print('#############', f)
    from shapely.geometry import Polygon
    polygon = Polygon([[f[0], f[1]], [f[0], f[3]], [f[2], f[3]], [f[2], f[1]]])
    ponto = polygon.centroid
    
    from meteostat import Point, Daily, Stations
    Stations.cache_dir = '/tmp'
    Daily.cache_dir = '/tmp'
    stations = Stations()
    stations = stations.nearby(ponto.y, ponto.x)
    station = stations.fetch(1)

    # Print DataFrame
    print(station)
    latitude = station['latitude'][0]
    longitude = station['longitude'][0]
    elevation = station['elevation'][0]
    distance = station['distance'][0]

    dataagora = datetime.now()
    start = datetime(dataagora.year-1, dataagora.month, dataagora.day)
    end = datetime(dataagora.year, dataagora.month, dataagora.day)

    # Create Point 
    vancouver = Point(latitude, longitude, elevation)

    # Get daily data 
    data = Daily(vancouver, start, end)
    data = data.fetch()

    res = pd.DataFrame(data)

    res.loc['Column_Total'] = res.sum(numeric_only=True, axis=0)
    volume = res.loc['Column_Total'][3]
    inicial = res.index

    unidades = ['tavg', 'prcp', 'wspd']
    legendas = []
    fig, ax = plt.subplots(figsize=(20, 10))

    cor = {'tavg' : 'red', 'prcp' : 'green', 'wspd': 'blue'}
    nomes = {'tavg' : 'Temperatura Média', 'prcp' : 'Preciptação Média', 'wspd': 'Vento Médio'}

    for unid in unidades:
        legendas.append(mpatches.Patch(color=cor[unid], label=nomes[unid]))
        data[unid].plot(ax=ax, color=cor[unid], label=data[unid].values[0])
    
    ax.margins(0.2)
    ax.legend(handles=legendas, loc='center left',bbox_to_anchor=(1, 0.5), prop={'size':30})
    plt.xlabel('Data Inicial :' + str(inicial[0]) + ' | Data Final :' + str(inicial[-2]))
    plt.savefig('/tmp/grafico.png', bbox_inches='tight')

    return volume, distance

def desenhaPag(resultados):
    print('################# INÍCIO desenhaPag #################')
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template("report.html")
    print('################# HTML CARREGADO #################')
    template_vars = {
                    'imagem1': '/tmp/figura.png',
                    'imagem2': '/tmp/grafico.png',
                    "dados" : resultados
                    }
    html_out = template.render(template_vars)
    from weasyprint import HTML
    HTML(string=html_out, base_url='.').write_pdf("/tmp/pagina.pdf")

def enviar(token, relid, url):
    new_pdf = PdfFileReader('/tmp/pagina.pdf')
    output = PdfFileWriter()

    for page in range(new_pdf.getNumPages()):
        output.addPage(new_pdf.getPage(page))

    buf = io.BytesIO()
    buf.seek(0)
    output.write(buf)
    buf.seek(0)

    head = 'Token ' + token
    headers = {'Authorization': head}

    files = {'upload_file': buf.read()}
    values = {'relid': relid}
    r = requests.post(url, files=files, data=values, headers=headers)

def main(aoi, relid, token, url):
    try:
        aoi = geojson.loads(aoi)
    except:
        aoi = json.dumps(aoi)
        aoi = geojson.loads(aoi)
    #print(aoi)
    for feature in aoi:
        area = ee.Geometry(feature['features'][0]['geometry'], opt_proj="EPSG:4326")

        dataagora = datetime.now()
        start = datetime(dataagora.year-1, dataagora.month-1, dataagora.day)
        end = datetime(dataagora.year, dataagora.month-1, dataagora.day)
        dataset = ee.ImageCollection('NASA_USDA/HSL/SMAP10KM_soil_moisture') \
            .filter(ee.Filter.date(start, end)) \
            .select('ssm')
        median = dataset.reduce(ee.Reducer.median())

        vetor = median.toInt8().reduceToVectors(
            geometry=area,
            crs='EPSG:4326',
            scale=10,
            geometryType='polygon',
            eightConnected=True,
            labelProperty='ssm',
            maxPixels=10000000,
            bestEffort=True)
        result = geemap.ee_export_geojson(vetor, '/tmp/var.geojson')
        result = geojson.loads(result)
        result = geopandas.GeoDataFrame.from_features(result).set_crs('epsg:4326')

        desenhaMapa(result)
        volume, distance = chuvas(result)
        
        volume = moeda(volume,'mm')
        distance = moeda(distance/1000, 'km')

        desenhaPag({'volume': volume, 'distance': distance})
        
        enviar(token, relid, url)