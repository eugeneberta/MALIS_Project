const http = require('http')
const fs = require('fs')

const k_renderUrl = 'http://192.168.0.42:12345';
let k_defaultParameters = 'product=airMaxOne&partsconfig=[]&width=256&height=256&format=jpg';
let g_cameraPoses = [{
    Tx: 2,
    Ty: 3,
    Tz: -2,
    Rx: 10,
    Ry: 10,
    Rz: 0,
    fieldOfView: 120
},
{
    Tx: 10,
    Ty: 0.55,
    Tz: -2.92,
    Rx: 15,
    Ry: 10,
    Rz: 0,
    fieldOfView: 60
}];

/**
 * Gets all snapshots with requested camera poses and writes them to file
 * @param {array} _cameraPoses Camera poses
 */
async function getAllSnapshots(_cameraPoses) {
    for (let i in g_cameraPoses) {
        let lParameters = k_defaultParameters + '&cameraparams=' + JSON.stringify(g_cameraPoses[i]);
        let lSnapshot = await httpGetSnap(k_renderUrl, lParameters);
        fs.writeFileSync('masks/PVS'+i + '.jpg', Buffer.from(Buffer.concat(lSnapshot.value)), 'binary');
    }
}

/**
 * Gets snapshot using provided parameters
 * @param {string} _renderUrl PVS Render URL for snapshot requests
 * @param {string} _parameters Snapshot parameters in PVS Render compliant format
 * @param {'GET', 'POST'} _requestMethod Request method to use with PVS Render
 */
function httpGetSnap(_renderUrl, _parameters, _requestMethod = 'GET') {
    let lURL = _renderUrl + "/snap";

    let lRequestOptions = {
      method: _requestMethod
    };

    if (_requestMethod == 'POST') {
        // Add headers for content
        lRequestOptions.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(_parameters)
        }
    } else if (_requestMethod == 'GET') {
        // Add request parameters to URL
        lURL += '?' + _parameters;
    } else {
        return Promise.reject({message: 'Request method should be GET or POST'});
    }
    
    return new Promise(function(_resolve, _reject) {
        const lRequest = http.request(lURL, lRequestOptions, (_response) => {
            let data = [];
            _response.on('data', (chunk) => {
                data.push(chunk);
            });
            _response.on('end', () => {
                if (_response.statusCode == 200) {
                    _resolve({value: data});
                } else {
                    _reject({parameters: _parameters, statusCode: _response.statusCode, httpGetSnapRejected: true});
                }
            });
        });
        
        lRequest.on('error', (e) => {
            _reject(e.message);
        });
        
        if (_requestMethod == 'POST') {
            // Write data to request body
            lRequest.write(_parameters);
        }
        lRequest.end();
        lRequest.shouldKeepAlive = false
    });
}

getAllSnapshots(g_cameraPoses);