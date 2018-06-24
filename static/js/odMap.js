function drawOdMap(zones, matrix){
	// zones should be an array of zone objects with attributes name and color
	// matrix should be a square matrix of size n×n
var width = 1800,
height = 1800,
outerRadius = Math.min(width, height) / 2 - 10,
innerRadius = outerRadius - 24;
 
// var formatPercent = d3.format(".1%");
 
var arc = d3.svg.arc()
.innerRadius(innerRadius)
.outerRadius(outerRadius);
 
var layout = d3.layout.chord()
.padding(.04)
.sortSubgroups(d3.descending)
.sortChords(d3.ascending);
 
var path = d3.svg.chord()
.radius(innerRadius);
 
d3.selectAll("#odMap svg").remove();
var svg = d3.select("#odMap").append("svg")
.attr("width", width)
.attr("height", height)
.append("g")
.attr("id", "circle")
.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
 
svg.append("circle")
.attr("r", outerRadius);
// d3.csv(inputPath+"zones.csv", function(zones) {
// 	d3.json(inputPath+primaryDate+ "/matrix.json", function(matrix) {	 
	// Compute the chord layout.
layout.matrix(matrix);
 
// Add a group per neighborhood.
var group = svg.selectAll(".group")
.data(layout.groups)
.enter().append("g")
.attr("class", "group")
.on("mouseover", mouseover);
 
// Add a mouseover title.
group.append("title").text(function(d, i) {
return zones[i].hover + ": " + Math.round(d.value) + " trips";
});
 
// Add the group arc.
var groupPath = group.append("path")
.attr("id", function(d, i) { return "group" + i; })
.attr("d", arc)
.style("fill", function(d, i) { return zones[i].color; });
 
// Add a text label.
var groupText = group.append("text")
.attr("x", 6)
.attr("dy", 15);
 
groupText.append("textPath")
.attr("xlink:href", function(d, i) { return "#group" + i; })
.text(function(d, i) { return zones[i].name; });
 
// Remove the labels that don't fit. :(
groupText.filter(function(d, i) { return groupPath[0][i].getTotalLength() / 2 - 16 < this.getComputedTextLength(); })
.remove();
 
// Add the chords.
var chord = svg.selectAll(".chord")
.data(layout.chords)
.enter().append("path")
.attr("class", "chord")
.style("opacity", .5)
.style("fill", function(d) { return zones[d.source.index].color; })
.attr("d", path);
 
// Add an elaborate mouseover title for each chord.
 chord.append("title").text(function(d) {
 if (d.source !=d.target){
 return zones[d.source.index].hover + " to " + zones[d.target.index].hover
 + ": " + Math.round(d.source.value)
 + "\n" + zones[d.target.index].hover + " to " + zones[d.source.index].hover
 + ": " + Math.round(d.target.value);
 } else {
 return zones[d.source.index].hover + " to " + zones[d.target.index].hover
 + ": " + Math.round(d.source.value)
 }
 });
 
function mouseover(d, i) {
chord.classed("fade", function(p) {
return p.source.index != i
&& p.target.index != i;
});
}
// 	});
// });

}