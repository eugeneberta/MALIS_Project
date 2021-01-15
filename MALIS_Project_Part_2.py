from scipy.spatial import distance
from PIL import Image
import numpy as np
import cv2 
import json
import requests
from io import BytesIO
import time
import matplotlib.pyplot as plt

### Set the parameters of the request to the Silhouette generator :

Silhouette_Generator_Url = 'http://192.168.0.42:12345'

# Width and Height of binary mask requested
binary_mask_width = 256
binary_mask_height = 256

# File format requested
binary_mask_format = 'jpg' 

# Parameters for the http request
defaultParameters = 'product=airMaxOne&partsconfig=[]&width='+str(binary_mask_width)+'&height='+str(binary_mask_height)+'&format='+binary_mask_format


# Name of the binary mask in input (the one we are going to fit with gradient descent), this is an output from the first part of the project :
input_name = 'mask_1.jpg'

# We open the input as an array
mask_NN = np.array(Image.open('/home/eugene/Desktop/MALIS_project/masks/'+input_name))

# We make it a binary image :
if len(mask_NN.shape) > 2 : 
    mask_NN = np.sum(mask_NN, axis=2)
    mask_NN = np.where(mask_NN > 127, 255, 0)


# getSnapshot function takes a set of parameters and returns a binary mask, provided by the silhouette generator.
def getSnapshot(_theta) :
    
    # We include the set of parameters theta to the request.
    parameters = defaultParameters + '&cameraparams=' + json.dumps(_theta, separators=(',', ':'))
    final_url = Silhouette_Generator_Url+"/snap"+"?"+parameters

    # HTTP request :
    r = requests.get(final_url)

    # Giving time for the server to answer, provided with too much requests, it can crash.
    time.sleep(0.2)

    # If the request is successful, we extract the binary mask
    if r.status_code == 200 :
        image = np.array(Image.open(BytesIO(r.content)))
    
    image = np.sum(image, axis=2)
    image = np.where(image >= 1, 255, 0)

    return image


# costFunction implements the distance metric we established thanks to the Hamming distance.
# given a set of parameters theta, it returns the distance to the mask we are trying to fit, that is the value of the cost function L(theta).
def costFunction(_theta) :
    # setting up the two binary masks to compare : 
    u = getSnapshot(_theta)
    v = mask_NN
    
    # The total distance is the sum of the hamming distance on each line :
    return sum(distance.hamming(u[i],v[i]) for i in range(len(mask_NN)))


# gradient function takes as an input a set of parameters theta and returns the gradient (6 dimensions) of the cost function in theta, that is nabla(L(theta))
# To make computation faster, the function also takes as an argument the value of the loss function in theta _error = L(theta), this value is computed earlier in our algo, we didn't wanted to compute it again.
def gradient(_theta, _error):
    
    theta_diff = _theta

    delta = 0.1

    ### We aproximate the gradient of L on each dimension of the set of parameters : Tx, Ty, Tz, Rx, Ry, Rz 

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


# We will now apply gradient descent to optimize the theta parameters.

def gradientDescent():
    
    # The algorithm usually takes 14 steps to end, we take the security to stop it after 20 iterations
    max_iteration = 20

    #Parameters for implementing backtracking line search :
    beta = 0.75
    alpha = 0.05
    t_init = 0.2

    # We need to start with a set of parameters that return an mask somwhere in the picture so that the distance can be computed.
    # For this reason, we will not start with a random guess but with a defined set of parameters.
    # Initial set of parameters for which we see the shoe :
    theta = {
    'Tx':-1,
    'Ty':0.5,
    'Tz':-2,
    'Rx':3,
    'Ry':10,
    'Rz':0,
    'fieldOfView':120
    }
    
    iteration = 0

    # We stock the error at each iteration in a list :
    error = [costFunction(theta)]
    
    # t : learning rate computed by backtracking line search.
    t = t_init

    # Our stopping criterion is base on the value of t, the learning rate computed by backtracking line search, this is explained in our report.
    while(iteration < max_iteration and t>1e-10):
        print("[Iteration number : "+str(iteration)+" starting]")
        
        grad = gradient(theta, error[-1])
        print("value of the gradient :"+str(grad))
        
        # Implementing backtracking line search to find the value of t for this iteration.
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

### Visualizing the binary mask estimated by the gradient descent, in the file output.jpg :
final_parameters = defaultParameters + '&cameraparams=' + json.dumps(final_theta, separators=(',', ':'))

final_url = Silhouette_Generator_Url+"/snap"+"?"+final_parameters
               
r = requests.get(final_url)
        
if r.status_code == 200:
    with open("/home/eugene/Desktop/MALIS_project/masks/output_"+input_name, 'wb') as f:
        for chunk in r:
            f.write(chunk)