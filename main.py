import take_picture
import time
import datetime


if __name__ == '__main__':
    while True:
        second = datetime.datetime.now().second
        if second < 8:
#             print('capture {0}!'.format(second))
            take_picture.upload_pciture()
            time.sleep(10)
        time.sleep(5)
#         print('skip {0}'.format(second))