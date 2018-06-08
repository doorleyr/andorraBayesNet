# -*- coding: utf-8 -*-


from flask import Flask
import matplotlib
import matplotlib.cm as cm
from flask import render_template
import numpy as np
from datetime import datetime
import json
import pickle
from threading import Lock
from flask import  session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

def getColor(value, cmap):
    col1=cmap(value)
    #col1Hex='#%02x%02x%02x' % (int(256*col1[0]), int(256*col1[1]), int(256*col1[2]))
    col1Hex=matplotlib.colors.rgb2hex(col1)
    return col1Hex

def background_thread():
    """send server generated events to clients."""
    count = 0
    while True:
        print("count"+str(count))
        pIndex=count%len(periods)
        for linkIndex in range(len(linksOut['features'])):
            linksOut['features'][linkIndex]['properties']['width']=1+15*(flows[periods[pIndex]]['Traffic'][linkIndex]/maxTraffic)
            linksOut['features'][linkIndex]['properties']['color']=getColor(flows[periods[pIndex]]['Traffic'][linkIndex]/maxTraffic, cmap)
        #updateSpatialData()        
        socketio.emit('backendUpdates',
                      {'data': {'links':linksOut, 'bounds':bounds}, 'count': count, 'period': datetime.utcfromtimestamp(periods[pIndex]).strftime("%Y-%m-%d %H:%M:%S")},
                      namespace='/test')
        socketio.sleep(1)
        count+=1

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'return to sender '+message['data'], 'count': session['receive_count']})
    print('Recieved from front end: ' + str(message['data']))
    
    
@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'You are connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

def updateSpatialData():
    return 0

# get the preprepared inputs: traffic, O-D and Beta data
netD=pickle.load( open( "data/network/netDriveJun18.p", "rb" ) )
nodeIDsD=pickle.load( open( "data/network/nodeIDsDriveJun18.p", "rb" ) )
nodesXYD=pickle.load( open( "data/network/nodesXYDriveJun18.p", "rb" ) )
flows=pickle.load(open( "data/results/andorraBayesSolution.p", "rb"))
zonesXY=pickle.load(open( "data/od/ODxy_Oct17.p", "rb"))
bounds=json.load(open( "data/geojson/bounds.geojson"))
periods=sorted(flows.keys())
maxTrips=np.max([np.max(flows[p]['OD']) for p in periods])
maxTraffic=np.max([np.max(flows[p]['Traffic']) for p in periods])

cmap=cm.get_cmap('cool')

pIndex=0

featureArray=[]
for linkIndex, row in netD.iterrows():
    feat={'type':'Feature','geometry':{'type':'LineString','coordinates': [[row['aNodeLon'], row['aNodeLat']], [row['bNodeLon'], row['bNodeLat']]]},'properties':{'type':row['type']
    , 'width':20*(flows[periods[pIndex]]['Traffic'][linkIndex]/maxTraffic)
    ,'color':getColor(flows[periods[pIndex]]['Traffic'][linkIndex]/maxTraffic, cmap)
    }}
    featureArray.extend([feat])
linksOut={'type':'FeatureCollection', 'features': featureArray}

#flowsOut={p: {'OD': [[flows[p]['newOD'][i,j] for j in range(len(flows[p]['newOD']))] for i in range(len(flows[p]['newOD']))], 'traffic': flows[p]['newTraffic']} for p in flows}
#
#featureArray=[]
#zonesLon, zonesLat= pyproj.transform(utm31N, wgs84, zonesXY[:,0],  zonesXY[:,1])
#for z in range(len(zonesLon)):
#    feat={'type':'Feature','geometry':{'type':'Point','coordinates': [zonesLon[z], zonesLat[z]]},'properties':{}}
#    featureArray.extend([feat])
#zonesOut={'type':'FeatureCollection', 'features': featureArray}


if __name__ == '__main__':
    socketio.run(app, debug=True) 
    