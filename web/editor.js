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

function formatTime(seconds) {
    var date = new Date(null);
    date.setSeconds(seconds); // specify value for SECONDS here
    var timeString = date.toISOString().substring(11, 11+8);
    return timeString;
}

var simplemde = null;
var currentPos = null;

function onKeyup(cm,event) {
    var pos = cm.getCursor();
    var lineCount = cm.lineCount();
    console.log('currentPos:',currentPos)
    console.log('Pos:',pos)

    direction = null
    if(event.key === 'ArrowDown' && pos.line === lineCount - 1 && currentPos && currentPos.ch == pos.ch) 
        direction = 'Next'
    else if (event.key === 'ArrowUp' && pos.line === 0)
        direction = 'Prev'

    if(direction) {
        ta = cm.getTextArea()
        var parent = ta.parentNode.parentNode;
        var nextRow = direction=='Next'? parent.nextElementSibling : parent.previousElementSibling
        if(nextRow ) {
            nextPara = nextRow.getElementsByClassName('paragraph')[0]
            turnOnEditor(nextPara.id)
        }

    }

}    

function onKeydown(cm,event) {
    var pos = cm.getCursor();
    var lineCount = cm.lineCount();
    currentPos = null   
    if(event.key === 'ArrowDown' && pos.line === lineCount - 1) 
        currentPos = pos;
}

function turnOnEditor(para_id) {
    if(simplemde) {
        simplemde.toTextArea();
        simplemde = null
    }
    simplemde = new SimpleMDE({ element: document.getElementById(para_id) });
    simplemde.codemirror.on('keydown', onKeydown);         
    simplemde.codemirror.on('keyup', onKeyup);         
    simplemde.codemirror.setCursor({line: 0, ch: 0});
    simplemde.codemirror.focus();
}

function sameRow(e1, e2) {
    while(e1 && e1.tagName !== 'TR') {
        e1 = e1.parentNode;
    }
    while(e2 && e2.tagName !== 'TR') {
        e2 = e2.parentNode;
    }
    return e1 === e2;
}

function getTextAreInRow(e) {
    while(e && e.tagName !== 'TR') {
        e = e.parentNode;
    }
    return e.getElementsByClassName('paragraph')[0];
}

function onRowClicked(e) {
    if(simplemde) {
        ta = simplemde.element
        if(sameRow(e.target, ta))
            return;
    }
    para_id = getTextAreInRow(e.target).id;

//                    player = document.getElementById('player');
//                    player.currentTime =  para.start_time;
//                    player.play();
    turnOnEditor(para_id);
}

function loadParagraphs(scriptData) {

    sc = document.getElementById('sc');
    scriptData.scripts.forEach(function(para) {
        var tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="timeline" width='50'>${para.start_timeline}</td>
            <td><textarea id="${para.index}" readonly class="paragraph">${para.text}</textarea></td>`;
        tr.onclick = onRowClicked                
        sc.appendChild(tr);
    })

    var paras =  document.getElementsByClassName('paragraph')
    for( ta of paras){
        ta.style.height = ta.scrollHeight + 'px';
    }
}


async function loadData() {

    var urlParams = new URLSearchParams(window.location.search);
    var item_name = urlParams.get('i');


    const [slide_text, script_text, timeline ] = await Promise.all([ 
            loadFile( 'data/slide/' + item_name + '.json'),
            loadFile( 'data/script_fixed/' + item_name + '.txt'),
            loadFile( 'data/script/' + item_name + '.jsonl')
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


    var scriptParagraphs = script_text.match(/[^\[]+\[[\d_]+\]\n\n/g);
    paragraphs =  scriptParagraphs.map(function(para) {
        var startIndex = para.indexOf('[');
        var endIndex = para.indexOf(']');
        return { 
            index: para.substring(startIndex + 1, endIndex), 
            text: para.substring(0, startIndex ) 
        }
    }); 

    for(i = 0; i < paragraphs.length; i++) {
        var para = paragraphs[i];
        var timelineItem = i > 0 ? timelineDictionary[ paragraphs[i-1].index] : null;
        if (timelineItem) {
            para.start_time = calcuateTime( timelineItem.index, timelineItem.end_time);

            para.start_timeline = formatTime(para.start_time);

        }
        else {
            para.start_timeline = '00:00:00'
            para.start_time = 0 
        }
        
    }

    return {
        slides: slideData,
        scripts: paragraphs,
        item:item_name            
    }    
}




var scriptData = {}
var player = null;

function setSlideText(currentTime) {
    for(i = 0; i < scriptData.slides.length; i++) {
        slide = scriptData.slides[i]; 
        if ( currentTime > slide.time && currentTime < (i < scriptData.slides.length -1 ? scriptData.slides[i+1].time: 9999999999)) {
//            var slideTextDiv = document.getElementById('slide_text');
//            slideTextDiv.innerHTML = marked.parse(slide.text); 
            simplemde.value(slide.text);
            
            break
        }
    }
}

function timeChanged(e) {
    var currentTime = player.currentTime;
    document.getElementById("demo").innerHTML = player.currentTime;
    var sc = document.getElementById('sc');
    var divs = sc.childNodes
    for (var i = 0; i < divs.length; i++) {
        var div = divs[i];
        para = div.data
        if (currentTime > para.start_time && currentTime < (i < divs.length - 1 ? divs[i+1].data.start_time : 9999999999)) {
            div.classList.add('highlight');
        }
        else {                    
            div.classList.remove('highlight');
        }
    }
    setSlideText(currentTime)
}        

async function onLoaded() {
    if(!sessionStorage.getItem('userId')) {
//        alert('Please sign into Google')
//        return
    }


    scriptData = await loadData();

    loadParagraphs(scriptData);
    
}

window.onload = onLoaded;

