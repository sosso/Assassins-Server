import base64
import os
import requests

def upload(base64img=None, file_body=None, file_path=None):
    if bool(os.environ.get('TEST_RUN', False)) or bool(os.environ.get('TEST_RUN_MIKE', False)):
        return 'http://i.imgur.com/4ZLv3.jpg'
    api_key = '6c17943562b05127a1a181b8d4cb58f5'
    if base64img is not None:
        pass
    elif file_body is not None:
        base64img = base64.b64encode(file_body)
    elif file_path is not None:
        file = open('test.png', 'rb')
        base64img = base64.b64encode(file.read())
    data = {'key':api_key, 'image':base64img}
    r = requests.post('http://api.imgur.com/2/upload.json', data=data)
    try: url = r.json['upload']['links']['original']
    
    except: url = None
    return url
    
if __name__ == '__main__':
    upload()
