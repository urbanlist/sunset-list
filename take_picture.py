from azure.cosmosdb.table.tableservice import TableService
from azure.storage.blob import BlockBlobService
from azure.cosmosdb.table.models import Entity
from azure.storage.file import ContentSettings
import io
import time
import numpy as np
from PIL import Image
import picamera
import pandas as pd
import sys
import time
import json


def get_reversed_unix_time():
    max_value = sys.maxsize
    time_data = time.time()
    return str(int(max_value-time_data))

def upload_pciture():
    stream = io.BytesIO()
    with picamera.PiCamera() as picam:
        picam.start_preview()
        picam.vflip = True
        time.sleep(2)
        picam.capture(stream, format='bmp')
        picam.stop_preview()
        picam.close()
    stream.seek(0)
    image = Image.open(stream)
    
    # resize
    image = image.resize((int(720/8), int(480/8)), Image.ANTIALIAS)
    
    with open('api_key.json', 'r') as f:
        app_key = json.loads(f.read())
        # stream image upload
        imagefile = io.BytesIO()
        image.save(imagefile, format='BMP')
        imagefile.seek(0)
        
        file_name = '{0}.bmp'.format(get_reversed_unix_time())
        block_blob_service = BlockBlobService(connection_string=app_key['azure_storage_connection'])
        blob = block_blob_service.create_blob_from_stream('nuknuk', file_name, imagefile)
        imagefile.close()
        
        file_url = 'https://urbanlist.blob.core.windows.net/nuknuk/{0}'.format(file_name)
        
        table_service = TableService(connection_string=app_key['azure_storage_connection'])
        task = {
            'PartitionKey': 'nyuknyuk',
            'RowKey': '{0}'.format(get_reversed_unix_time()), 
            'Green' : 0,
            'Red' : 0,
            'Blue': 0,
            'FilePath':file_url}
        table_service.insert_entity('nuknuk', task)
    
    stream.close()

if __name__ == '__main__':
    upload_pciture()