var Msg
var map
var firstTime=1
var initialised=0
var chromaScale = chroma.scale(['#62B1F6', '#DB70DB','#2E0854']);
var myCustomControl

//Maptastic("map");

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

function initialMap(options){
  // Initialise the map  
  map = new mapboxgl.Map({
      container: 'map', // container id
      style: options.style,
      center: options.center, // starting position [lng, lat]
      zoom: options.zoom ,// starting zoom
      pitch: options.pitch
  // map = new mapboxgl.Map({
  //   container: 'map', // container id
  //   style: 'mapbox://styles/mapbox/dark-v9', // stylesheet location
  //   center: [1.521835, 42.506317], // starting position [lng, lat]
  //   zoom: 14 ,// starting zoom
  //   pitch:0
  }); 

myCustomControl = new MyCustomControl();
map.addControl(myCustomControl, 'top-left');
}



$(document).ready(function(){ 

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
              socket.emit('initialDataRequest', {data: 'Front end wants the initial data'});
              socket.emit('my_event', {data: 'Front end says: I\'m connected!'});
                
            });
            // Event handler for server sent data.
            // The callback function is invoked whenever the server emits data
            // to the client. 
            socket.on('my_response', function(msg) {           
                console.log(msg.data)
            });

            socket.on('initialData', function(msg) {           
                console.log(msg.data);
                initialMap(msg.mapOptions);
                //Msg=msg;                
                // map.on('load', function () {
                // });               
            });

            socket.on('backendUpdates', function(msg) {           
                console.log('Received an update');
                makeMap(msg);
                drawOdMap(msg.data.od.zones, msg.data.od.matrix);
            });

});

function makeMap(thisMsg) {  
  // map.on('style.load', function () {
  data=thisMsg.data;
  period=thisMsg.period;

  for (var key in data.spatial) {
    if (typeof map.getSource(key) == "undefined"){
      console.log('Creating '+key+' for first time')
      map.addSource(key, { type: 'geojson', data: data.spatial[key] });
      console.log(data.spatial[key])
      if (data.spatial[key].features[0].geometry.type=='LineString'){
        map.addLayer({
              "id": key,
              "type": "line",
              "source": key,
              "layout": {
                "line-join": "round",
                "line-cap": "round"},
              "paint": {
                  "line-width":['+',1,['*', 10, ['get', 'scale']]],
                  "line-color":["case", 
                    ['>',['number',['get', 'scale']],0.8],['rgb', 200,0,0],
                    ['>',['number',['get', 'scale']],0.6],['rgb', 200,100,0],
                    ['>',['number',['get', 'scale']],0.4],['rgb', 200,200,0],
                    ['>',['number',['get', 'scale']],0.2],['rgb', 100,200,0],
                    ['rgb', 0,200,0]],
                  "line-opacity":1
              }    
          });
      }
      if (data.spatial[key].features[0].geometry.type=='Polygon'){
          map.addLayer({
                    "id": key,
                    "type": "fill",
                    "source": key,
                    'paint': {
                    'fill-color': '#fff',
                    'fill-opacity': 0.1
                  }           
          });
      }

      ////////Toggle capability//////
      var id = key;

      var link = document.createElement('a');
      link.href = '#';
      link.className = 'active';
      link.textContent = id;

      link.onclick = function (e) {
          var clickedLayer = this.textContent;
          e.preventDefault();
          e.stopPropagation();

          var visibility = map.getLayoutProperty(clickedLayer, 'visibility');

          if (visibility === 'visible') {
              map.setLayoutProperty(clickedLayer, 'visibility', 'none');
              this.className = '';
          } else {
              this.className = 'active';
              map.setLayoutProperty(clickedLayer, 'visibility', 'visible');
          }
      };

      var layers = document.getElementById('menu');
      layers.appendChild(link);
      ////////Toggle capability//////

    }
    else{
      //update data only
      map.getSource(key).setData(data.spatial[key]); 
      console.log('updating '+key) 
    }
    if (typeof period != "undefined"){
      myCustomControl.container.textContent = period;}

    
  }

}

  