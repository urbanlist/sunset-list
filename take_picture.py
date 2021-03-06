#!/usr/bin/python3

import sys
sys.path.append('/home/pi/projects/sunset-list')
    
from azure.cosmosdb.table.tableservice import TableService
from azure.storage.blob import BlockBlobService
from azure.cosmosdb.table.models import Entity
from azure.storage.file import ContentSettings
import os
import io
import time
import datetime
import numpy as np
import pandas as pd
from PIL import Image
import picamera
import time
import json
import weather
import analysis_sky
import logging
import traceback


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

def get_picture_stream():
    stream = io.BytesIO()
    with picamera.PiCamera() as picam:
        picam.start_preview()
        picam.vflip = False
        picam.iso = 100
        
        if (os.path.isfile('/home/pi/projects/sunset-list/task.json')):
            with open('/home/pi/projects/sunset-list/task.json', 'r') as f:
                task = json.loads(f.read())
                if task['SkyStatus'] == 'SKY_A01':
                    picam.awb_mode = 'sunlight'
                elif  task['SkyStatus'] == 'SKY_A02':
                    picam.awb_mode = 'sunlight'
                else:
                    picam.awb_mode = 'auto'
        else:
            picam.awb_mode = 'auto'
        
        time.sleep(4)
        picam.capture(stream, format='bmp')
        picam.stop_preview()
        picam.close()
    stream.seek(0)
    return stream

def get_image_from_stream_as_resize(stream):
    image = Image.open(stream)
    
    # resize
    image = image.resize((int(720/8), int(480/8)), Image.ANTIALIAS)
    
    # 아래 45 픽셀 삭제
    rgb_array = np.asarray(image)
    crop_image = rgb_array[:45]
    im = Image.fromarray(crop_image)
    image = im
    return image, rgb_array

def get_dataframe_from_rgb_array(rgb_array):
    # 데이터를 하나의 배열로 정리
    image_dataset = []
    for row in rgb_array:
        for item in row:
            image_dataset.append(item)
    image_dataset = np.array(image_dataset)
    df = pd.DataFrame(image_dataset, columns=['red','green','blue'])
    return df

def upload_pciture():
    now = datetime.datetime.now()
    row_key = get_reversed_unix_time()
    
    stream = get_picture_stream()
    image, rgb_array = get_image_from_stream_as_resize(stream)
    
    df = get_dataframe_from_rgb_array(rgb_array)
    min_rgb, max_rgb = analysis_sky.analysis_rgb(df)
    
    with open('/home/pi/projects/sunset-list/api_key.json', 'r') as f:
        app_key = json.loads(f.read())
        table_service = TableService(connection_string=app_key['azure_storage_connection'])
        
        task = {
            'PartitionKey': 'nyuknyuk',
            'RowKey': '{0}'.format(row_key),
            'FilePath':None,
            'SkyStatus':'none',
            'Temperature': None,
            'RainType': None,
            'WindSpeed': None,
            'MinVectorRed':int(min_rgb.red),
            'MinVectorGreen':int(min_rgb.green),
            'MinVectorBlue':int(min_rgb.blue),
            'MaxVectorRed':int(max_rgb.red),
            'MaxVectorGreen':int(max_rgb.green),
            'MaxVectorBlue':int(max_rgb.blue)
        }
        
        # 날씨 데이터
        if now.minute % 5 == 0:
            try:
                sky_status, temp, rain_type, wind_speed = weather.load_weather_data()
                task['SkyStatus'] = sky_status
                task['Temperature'] = temp
                task['RainType'] = rain_type
                task['WindSpeed'] = wind_speed
                with open('/home/pi/projects/sunset-list/task.json', 'w') as f:
                    json.dump(task, f)
            except:
                pass
        else:
            if (os.path.isfile('/home/pi/projects/sunset-list/task.json')):
                with open('/home/pi/projects/sunset-list/task.json', 'r') as f:
                    dump_task = json.loads(f.read())
                    task['SkyStatus'] = dump_task['SkyStatus']
                    task['Temperature'] = dump_task['Temperature']
                    task['RainType'] = dump_task['RainType']
                    task['WindSpeed'] = dump_task['WindSpeed']

        # 밤 낮 구분
        if is_night(df):
            table_service.insert_entity('nuknuk', task)
        else:
            # stream image upload
            imagefile = io.BytesIO()
            image.save(imagefile, format='BMP')
            imagefile.seek(0)

            file_name = '{0}.bmp'.format(row_key)
            block_blob_service = BlockBlobService(connection_string=app_key['azure_storage_connection'])
            blob = block_blob_service.create_blob_from_stream('nuknuk', file_name, imagefile)
            imagefile.close()

            file_url = 'https://urbanlist.blob.core.windows.net/nuknuk/{0}'.format(file_name)
            task['FilePath'] = file_url
            table_service.insert_entity('nuknuk', task)
    
    stream.close()

if __name__ == '__main__':
#         f.write('run: '+str(datetime.datetime.now())+'\n')
    try:
        upload_pciture()
    except Exception as e:
        with open('/home/pi/projects/sunset-list/log.log', 'a') as f:
            f.write(str(datetime.datetime.now())+' except: '+str(e)+'\n')
            traceback.print_exc(file=f)
            f.write('\n')