import requests
import base64

def upload(base64img=None, file_path=None):
    api_key = '6c17943562b05127a1a181b8d4cb58f5'
    if base64img is not None:
        pass
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
