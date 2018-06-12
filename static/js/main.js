var Msg
var firstTime=1

Maptastic("map");

class MyCustomControl {
  onAdd(map){
    this.map = map;
    this.container = document.createElement('div');
    this.container.className = 'my-custom-control';
    this.container.textContent = 'My custom control';
    return this.container;
  }
  onRemove(){
    this.container.parentNode.removeChild(this.container);
    this.map = undefined;
  }
}

mapboxgl.accessToken = 'pk.eyJ1IjoiZG9vcmxleXJtaXQiLCJhIjoiY2pnNnh5NHJwOHp2YzJ4bXNkdWZyNWd3ZSJ9.am1Wub7LEzVfZKHAdRZe4g';

var map = new mapboxgl.Map({
    container: 'map', // container id
    style: 'mapbox://styles/mapbox/dark-v9', // stylesheet location
    center: [1.521835, 42.506317], // starting position [lng, lat]
    zoom: 14 ,// starting zoom
    pitch:0
}); 

const myCustomControl = new MyCustomControl();

map.addControl(myCustomControl, 'top-left');


$(document).ready(function(){ 
            // Initialise the map
             

            /////////////////////////////////////////
            //Open the conections with the back end
            /////////////////////////////////////////

            // Use a "/test" namespace.
            // An application can open a connection on multiple namespaces, and
            // Socket.IO will multiplex all those connections on a single
            // physical channel. If you don't care about multiple channels, you
            // can set the namespace to an empty string.
            namespace = '/test';
            // Connect to the Socket.IO server.
            // The connection URL has the following format:
            //     http[s]://<domain>:<port>[/<namespace>]
            var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
            // Event handler for new connections.
            // The callback function is invoked when a connection with the
            // server is established.
            socket.on('connect', function() {
                socket.emit('my_event', {data: 'Front end says: I\'m connected!'});
            });
            // Event handler for server sent data.
            // The callback function is invoked whenever the server emits data
            // to the client. The data is then displayed in the "Received"
            // section of the page.
            socket.on('my_response', function(msg) {           
                console.log(msg.data)
            });

            socket.on('backendUpdates', function(msg) {               
                Msg=msg
                console.log('Received an update')
                makeMap()
            });

});

function makeMap() {  
  // map.on('style.load', function () {
  data=Msg.data;
  linksData=data.links;
  boundsData=data.bounds;
  period=Msg.period;

  
  if (firstTime==1) {
    map.addSource('linksSource', { type: 'geojson', data: linksData });
    map.addLayer({
          "id": "links",
          "type": "line",
          "source": 'linksSource',
          "layout": {
            "line-join": "round",
            "line-cap": "round"},
          "paint": {
              // "line-width":['get', '1472713200', ['get', 'width']],
              "line-width":['get', 'width'],
              "line-color":['get', 'color'],
              "line-opacity":1
          }    
      });
    // map.addLayer({
    //       "id": "bounds",
    //       "type": "fill",
    //       "source": { type: 'geojson', data: boundsData },
    //       'paint': {
    //         'fill-color': '#fff',
    //         'fill-opacity': 0.1
    //     }
             
    //   });


    firstTime=0;
  }
  //update layer based on latest data from backend
  map.getSource('linksSource').setData(linksData);
  console.log(period);
  myCustomControl.container.textContent = period;


}

  