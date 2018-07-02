#!/usr/bin/python3

import sys
sys.path.append('/home/pi/projects/sunset-list')
    
from azure.cosmosdb.table.tableservice import TableService
from azure.storage.blob import BlockBlobService
from azure.cosmosdb.table.models import Entity
from azure.storage.file import ContentSettings
import weather
import io
import time
import datetime
import numpy as np
import pandas as pd
from PIL import Image
import picamera
import time
import json

def get_reversed_unix_time():
    max_value = sys.maxsize
    time_data = time.time()
    return str(int(max_value-time_data))

def is_night(df):
    if (np.mean(df.red) < 10.0 and
        np.mean(df.blue) < 10.0 and
        np.mean(df.green) < 10.0):
        return True
    return False

def upload_pciture():
    now = datetime.datetime.now()
    stream = io.BytesIO()
    with picamera.PiCamera() as picam:
        picam.start_preview()
        picam.vflip = False
        time.sleep(2)
        picam.capture(stream, format='bmp')
        picam.stop_preview()
        picam.close()
    stream.seek(0)
    image = Image.open(stream)
    
    # resize
    image = image.resize((int(720/8), int(480/8)), Image.ANTIALIAS)
    
    # 아래 45 픽셀 삭제
    im_data = np.asarray(image)
    crop_image = im_data[:45]
    im = Image.fromarray(crop_image)
    image = im
    
    # 데이터를 하나의 배열로 정리
    image_dataset = []
    for row in im_data:
        for item in row:
            image_dataset.append(item)
    image_dataset = np.array(image_dataset)
    df = pd.DataFrame(image_dataset, columns=['red','green','blue'])
    
    with open('/home/pi/projects/sunset-list/api_key.json', 'r') as f:
        app_key = json.loads(f.read())
        table_service = TableService(connection_string=app_key['azure_storage_connection'])
        
        task = {
            'PartitionKey': 'nyuknyuk',
            'RowKey': '{0}'.format(get_reversed_unix_time()),
            'FilePath':None,
            'SkyStatus':'none',
            'Temperature': None,
            'RainType': None,
            'WindSpeed': None
        }
        
        if is_night(df):
            table_service.insert_entity('nuknuk', task)
        else:
            # stream image upload
            imagefile = io.BytesIO()
            image.save(imagefile, format='BMP')
            imagefile.seek(0)

            file_name = '{0}.bmp'.format(get_reversed_unix_time())
            block_blob_service = BlockBlobService(connection_string=app_key['azure_storage_connection'])
            blob = block_blob_service.create_blob_from_stream('nuknuk', file_name, imagefile)
            imagefile.close()

            file_url = 'https://urbanlist.blob.core.windows.net/nuknuk/{0}'.format(file_name)
            task['FilePath'] = file_url

            # 날씨 데이터
            if now.minute % 5 == 0:
                try:
                    sky_status, temp, rain_type, wind_speed = weather.load_weather_data()
                    task['SkyStatus'] = sky_status
                    task['Temperature'] = temp
                    task['RainType'] = rain_type
                    task['WindSpeed'] = wind_speed
                    
                    table_service.insert_entity('nuknuk', task)
                except:
                    table_service.insert_entity('nuknuk', task)
            else:
                table_service.insert_entity('nuknuk', task)
    
    stream.close()

if __name__ == '__main__':
    with open('/home/pi/projects/sunset-list/log.log', 'a') as f:
#         f.write('run: '+str(datetime.datetime.now())+'\n')
        try:
            upload_pciture()
        except Exception as e:
            f.write(str(datetime.datetime.now())+' except: '+str(e)+'\n')