import json
import requests

renderUrl = 'http://192.168.0.42:12345'
defaultParameters = 'product=airMaxOne&partsconfig=[]&width=256&height=256&format=jpg'

cameraPoses = [{'Tx': -1,
 'Ty': 2.5,
 'Tz': -2.5,
 'Rx': 5,
 'Ry': 5,
 'Rz': 0.0,
 'fieldOfView': 120}]


def getSnapshots(_cameraPoses) :
    
    
    for i in range(len(_cameraPoses)):
      parameters = defaultParameters + '&cameraparams=' + json.dumps(_cameraPoses[i], separators=(',', ':'))

      final_url = renderUrl+"/snap"+"?"+parameters
               
      r = requests.get(final_url)
        
      if r.status_code == 200:
        with open("PVS_"+str(i)+".jpg", 'wb') as f:
          for chunk in r:
            f.write(chunk)


getSnapshots(cameraPoses)