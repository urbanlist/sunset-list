import sys
from PIL import Image
import time
import io
import picamera
from sklearn.cluster import DBSCAN
import numpy as np
import pandas as pd
import take_picture

def analysis_rgb(df):
    # create model and prediction
    model = DBSCAN(eps=3, min_samples=5)
    predict = pd.DataFrame(model.fit_predict(df))
    predict.columns = ['predict']

    # concatenate labels to df as a new column
    r = pd.concat([df,predict],axis=1)
    
    # 가장 많은 Count를 가진 predict의 index를 구해보자.
    tmp = {}
    for idx in set(r['predict']):
        tmp[idx] = len(r[r['predict'] == idx])
    max_idx = sorted(tmp, key=lambda i:tmp[i], reverse=True)[0]
    liner_data = r[r['predict'] == max_idx]
    
    # min, max rgb를 구해보자
    max_value = 0
    max_idx = 0
    min_value = sys.maxsize
    min_idx = 0

    for idx, row in liner_data.iterrows():
        val = row['red']*row['green']*row['blue']
        if max_value < val:
            max_value = val
            max_idx = idx
            continue
        if min_value > val:
            min_value = val
            min_idx = idx
            continue
    
    min_rgb = liner_data.iloc[min_idx]
    max_rgb = liner_data.iloc[max_idx]
    
    return (min_rgb, max_rgb)

if __name__ == '__main__':
    stream = take_picture.get_picture_stream()
    image, rgb_array = take_picture.get_image_from_stream_as_resize(stream)
    df = take_picture.get_dataframe_from_rgb_array(rgb_array)
    
    min_rgb, max_rgb = analysis_rgb(df)
    print(min_rgb)
    print(max_rgb)