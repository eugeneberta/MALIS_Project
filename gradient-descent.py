from scipy.spatial import distance
from PIL import Image
import numpy as np
import cv2 
import json
import requests
from io import BytesIO
import time
import matplotlib.pyplot as plt

renderUrl = 'http://192.168.0.42:12345'
defaultParameters = 'product=airMaxOne&partsconfig=[]&width=256&height=256&format=jpg'

input_name = 'mask_1.jpg'

mask_NN = np.array(Image.open('/home/eugene/Desktop/MALIS_project/masks/'+input_name))

if len(mask_NN.shape) > 2 : 
    mask_NN = np.sum(mask_NN, axis=2)
    mask_NN = np.where(mask_NN > 127, 255, 0)



def getSnapshot(_cameraPoses) :
    
    parameters = defaultParameters + '&cameraparams=' + json.dumps(_cameraPoses, separators=(',', ':'))
    final_url = renderUrl+"/snap"+"?"+parameters

    r = requests.get(final_url)

    time.sleep(0.2)

    if r.status_code == 200 :
        image = np.array(Image.open(BytesIO(r.content)))
    
    image = np.sum(image, axis=2)
    image = np.where(image >= 1, 255, 0)

    return image



def costFunction(_theta) :
    u = getSnapshot(_theta)
    v = mask_NN
    
    return sum(distance.hamming(u[i],v[i]) for i in range(len(mask_NN)))


def gradient(_theta, _error):
    
    theta_diff = _theta

    delta = 0.1

    theta_diff['Tx']+=delta
    grad_Tx = (costFunction(theta_diff)-_error)/delta
    theta_diff['Tx']-=delta

    theta_diff['Ty']+=delta
    grad_Ty = (costFunction(theta_diff)-_error)/delta
    theta_diff['Ty']-=delta

    theta_diff['Tz']+=delta
    grad_Tz = (costFunction(theta_diff)-_error)/delta
    theta_diff['Tz']-=delta

    theta_diff['Rx']+=delta
    grad_Rx = (costFunction(theta_diff)-_error)/delta
    theta_diff['Rx']-=delta

    theta_diff['Ry']+=delta
    grad_Ry = (costFunction(theta_diff)-_error)/delta
    theta_diff['Ry']-=delta

    theta_diff['Rz']+=delta
    grad_Rz = (costFunction(theta_diff)-_error)/delta
    theta_diff['Rz']-=delta
    
    return [grad_Tx, grad_Ty, grad_Tz, grad_Rx, grad_Ry, grad_Rz]


# We will now apply gradient descent to optimize the camera pose parameters.
# We need to start with a set of parameters that return an mask somwhere in the picture so that the hausdorff distance can be computed.
# For this reason, we will not start with a random guess but with a defined set of parameters.


def gradientDescent():
    
    max_iteration = 50
    target_error = 1

    #Parameters for implementing backtracking line search :
    beta = 0.75
    alpha = 0.05
    t_init = 0.5

    # Initial set of parameters for which we see the shoe :
    theta = {
    'Tx':-2,
    'Ty':2,
    'Tz':-2,
    'Rx':10,
    'Ry':10,
    'Rz':0,
    'fieldOfView':120
    }
    
    iteration = 0
    error = [costFunction(theta)]
    t = t_init

    while(error[-1] > target_error and iteration < max_iteration and t>1e-10):
        print("[Iteration number : "+str(iteration)+" starting]")
        
        grad = gradient(theta, error[-1])
        print("value of the gradient :"+str(grad))
        
        # Implementing backtracking line search :
        t = t_init

        update = {'Tx':theta['Tx']-t*grad[0],
        'Ty':theta['Ty']-t*grad[1],
        'Tz':theta['Tz']-t*grad[2],
        'Rx':theta['Rx']-t*grad[3],
        'Ry':theta['Ry']-t*grad[4],
        'Rz':theta['Rz']-t*grad[5],
        'fieldOfView':120}

        while(costFunction(update) > (error[-1] - alpha*t*np.matmul(grad, grad))):
            t = beta*t
            update = {'Tx':theta['Tx'] - t*grad[0],
            'Ty':theta['Ty'] - t*grad[1],
            'Tz':theta['Tz'] - t*grad[2],
            'Rx':theta['Rx'] - t*grad[3],
            'Ry':theta['Ry'] - t*grad[4],
            'Rz':theta['Rz'] - t*grad[5],
            'fieldOfView':120}

        print("Learning rate for this iteration :"+str(t))
        

        theta['Tx'] -= t*grad[0]
        theta['Ty'] -= t*grad[1]
        theta['Tz'] -= t*grad[2]
        theta['Rx'] -= t*grad[3]
        theta['Ry'] -= t*grad[4]
        theta['Rz'] -= t*grad[5]
        
        iteration += 1
        error.append(costFunction(theta))

        print("Iteration ending, error = "+str(error[-1])+'\n')

    
    print("\nWe have reached iteration number "+str(iteration)+" and error = "+str(error)+", end of the algorithm")

    return theta, error



final_theta, error = gradientDescent()

parameters = defaultParameters + '&cameraparams=' + json.dumps(final_theta, separators=(',', ':'))

final_url = renderUrl+"/snap"+"?"+parameters
               
r = requests.get(final_url)
        
if r.status_code == 200:
    with open("/home/eugene/Desktop/MALIS_project/masks/output.jpg", 'wb') as f:
        for chunk in r:
            f.write(chunk)