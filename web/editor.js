async function loadFile(filePath) {
    var xhr = new XMLHttpRequest();            
    xhr.open('GET', encodeURI(filePath), true);
    return new Promise(function(resolve, reject) {
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var fileContents = xhr.responseText;
                resolve(fileContents)
            }
            else if (xhr.readyState === 4 && xhr.status !== 200){
                reject('Error loading file')
            }
        };
        xhr.send();
    })
}


function calcuateTime(index, timestamp) {
    sec = index.split('_')[0];
    ts = timestamp.split(',')[0].split(':')
    return (parseInt(sec) - 1) * 60 * 20 + parseInt(ts[0]) * 60 * 60 + parseInt(ts[1]) * 60 + parseInt(ts[2])
}

async function loadData() {
    const [slide_text, script_text, timeline ] = await Promise.all([ 
            loadFile('slide_text.json'),
            loadFile('2019-2-15 心mp4.txt'),
            loadFile('2019-2-15 心mp4.jsonl')
             ])
    var slideData = JSON.parse(slide_text);
    var timelineData = timeline.split('\n').map(function(line) {
        try {
            return JSON.parse(line)
        } catch (e) {
            console.log('Error parsing line', line)
            return null
        }
    }
    )

    var timelineDictionary = {};
    timelineData.forEach(function(item) {
        if(item && item.index)
            timelineDictionary[item.index] = item;
    });

    var slideDictionary = {};
    slideData.forEach(function(item) {
        if(item && item.index)
            slideDictionary[item.index] = item;
    });            

    var scriptParagraphs = script_text.split('\n\n');
    paragraphs =  scriptParagraphs.map(function(para) {
        var startIndex = para.indexOf('[');
        var endIndex = para.indexOf(']');
        return { 
            index: para.substring(startIndex + 1, endIndex), 
            text: para.substring(0, startIndex - 1) 
        }
    }); 

    for(i = 0; i < paragraphs.length; i++) {
        var para = paragraphs[i];
        var timelineItem = i > 0 ? timelineDictionary[ paragraphs[i-1].index] : null;
        if (timelineItem) 
            para.start_time = calcuateTime( timelineItem.index, timelineItem.end_time);
        else
            para.start_time = 0 
        
    }

    return {
        slides: slideDictionary,
        scripts: paragraphs            
    }    
}




var scriptData = {}
var player = null;

function setSlideText(index) {
    var slideText = scriptData.slides[index].text;
    var slideTextDiv = document.getElementById('slide_text');
    slideTextDiv.innerHTML = slideText;
}

function timeChanged(e) {
// Display the current position of the video in a <p> element with id="demo"
    document.getElementById("demo").innerHTML = player.currentTime;
    var sc = document.getElementById('sc');
    var divs = sc.getElementsByTagName('div');
    for (var i = 0; i < divs.length; i++) {
        var div = divs[i];
        para = div.data
        next_para_start_time = i < divs.length - 1 ? divs[i+1].data.start_time : 9999999999;
        if (player.currentTime > para.start_time && player.currentTime < next_para_start_time) {
            setSlideText(para.index);
            div.classList.add('highlight');
            break
        }
        else {                    
            div.classList.remove('highlight');
        }
    }
}        

async function onLoaded() {
    scriptData = await loadData();
    var sc = document.getElementById('sc');
    scriptData.scripts.forEach(function(para) {
        var div = document.createElement('div');
        div.innerHTML = para.text;
        div.style.display = 'block';
        div.style.margin = '10px';
        div.style.cursor = 'pointer';
        div.data = para
        div.onclick = function(e) {
            para = e.target.data;
            player = document.getElementById('player');
            player.currentTime =  para.start_time;
            player.play();
            setSlideText(para.index);
        }
        sc.appendChild(div);
    });
    setSlideText(scriptData.scripts[0].index);

    player = document.getElementById('player'); 
    player.ontimeupdate = function() {timeChanged()};


}

window.onload = onLoaded;

