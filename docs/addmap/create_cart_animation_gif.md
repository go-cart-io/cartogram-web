# Creating a cartogram animation GIF

This guide will help you to create a cartogram animation GIF (e.g. [World Map](https://thumbs.gfycat.com/FriendlyEnragedCrayfish-small.gif)).
This guide assumes that you are already fairly familiar with setting up the website code for local testing and development by following the instructions here https://github.com/jansky/cartogram-docker.

## Contents
[1. Downloading the cartogram animation frames as SVGs](#1-downloading-the-cartogram-animation-frames-as-svgs)<br/>
[2. Converting the SVGs into PNGs](#2-converting-the-svgs-into-pngs)<br/>
[3. Compiling the PNGs into a GIF](#3-compiling-the-pngs-into-a-gif)<br/>


## 1. Downloading the cartogram animation frames as SVGs

First, you will need to start up the website on your machine locally. 

```
$ cd cartogram-docker/
$ docker-compose up
```

Open `cartogram-docker/cartogram-web/internal/static/cartogram2.js` in your preferred text editor or IDE.

### 1.1 Adding the `downloadSVG()` function

Find the method `displayVersionSwitchButtons()` of the class `Cartogram`, which might be on line ~2500. You will now create a function in this method that downloads the frames of the cartogram animation as SVGs. 

On line ~2548, right before the end of the method, insert the following `downloadSVG()` function.

```
// Creates a script element for FileSaver.js, which helps to save files on the client-side.
let script2 = document.createElement('script');
script2.src = '/static/FileSaver.js';
document.getElementsByTagName("head")[0].appendChild(script2);

// Create variables
let cartArea = document.getElementById('cartogram-area');
let svgElem = cartArea.getElementsByTagName('svg')[0];
let totalDuration = 10000; // Total duration of all animations
let frameRate = 500; // Milliseconds per frame (50 milliseconds is 1/20th of a second i.e. 20fps)
let totalFrames = totalDuration / frameRate;
let currentFrames = 0;
let id = 0; // id for SVGs

function downloadSVG() {

    // Save SVG element and namespace to a Blob object
    let svgHTML = svgElem.innerHTML;
    svgHTML = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">' + svgHTML + '<\/svg>';
    let svgBlob = new Blob([svgHTML], {type: "image/svg+xml, charset=utf-8"}); // create a "blob object" storing the svg
    
    // save SVG file
    function saveSVG () {
      saveAs(svgBlob, "frame_" + id + ".svg"); // from FileSaver.js
      id++;
      console.log(id);
    }
    setTimeout(saveSVG, totalDuration); // Set delay on saving as it interrupts the transition

    // Return when the number of total frames has been reached
    if (currentFrames >= totalFrames) return;
    currentFrames++;

    // Call downloadSVG() recursively within intervals of the frameRate
    setTimeout(downloadSVG, frameRate);
}
```
On line ~2535, insert the code `downloadSVG();` so that the `downloadSVG()` function is called when an option is selected from the dropdown menu (e.g. Land Area/Population/GDP).

```
select.onchange = (function(cartogram_inst){

  return function(_e) {
    downloadSVG();
    cartogram_inst.switchVersion(this.value);
  };   
}(this));
```

Download `FileSaver.js` from https://github.com/eligrey/FileSaver.js/tree/master/dist and move it to `cartogram-docker/cartogram-web/internal/static/`.

### 1.2 Downloading the SVGs from your local website

Visit your locally-hosted website and select a country. Select an option from the dropdown menu (e.g. Land Area/Population/GDP) and the SVG frames for that animation should get downloaded onto your computer.


## 2. Converting the SVGs into PNGs

Open the SVGs in Inkscape and ensure that each of their canvas extents fit to the SVG object (no smaller). Export the SVGs to PNGs using Inkscape or another software.


## 3. Compiling the PNGs into a GIF

Use a GIF-creating website (e.g. https://gifmaker.me) to compile your PNGs into a GIF.

You may also upload your GIF to a website like https://gfycat.com/upload for public viewing.
