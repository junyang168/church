
async function loadFile(type, item_name, ext) {
    try {
        const response = await fetch(api_prefix + 'load/' + type + '/' + item_name + '/' + ext);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data =  await response.json();
        return data
    } catch (error) {
        console.error(error);
    }      
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
    current_para = document.getElementById(para_id)
    if(simplemde) {
        simplemde.toTextArea();
        simplemde = null
    }
    simplemde = new SimpleMDE({ 
        toolbar: ["bold", "italic", "strikethrough", 
        {
            name: "undo",
            action: function(editor) {
                editor.codemirror.undo();
            },
            className: "fa fa-undo", // Font Awesome icon class
            title: "Undo",
        },        
        "link", "image","quote", "horizontal-rule", "preview", "side-by-side", "fullscreen",
        {
            name: "play",
            action: function(editor) {
                para = editor.element.data;
                player = document.getElementById('player');
                syncPlayerSlide( para.start_time );
                player.play();
            },
            title: "Play Video",
            className: "fa fa-video-camera", // Optional
          },
  
    ],
    status: false,
        element: current_para , 
    });
    simplemde.codemirror.on('keydown', onKeydown);         
    simplemde.codemirror.on('keyup', onKeyup);         
    simplemde.codemirror.on('change', function() {
        var updatedContent = simplemde.value();
        var para = simplemde.element.data;
        para.text = updatedContent;

        if(!pendingSave) {
            pendingSave = true;
            setTimeout(saveScript, 10000);
        }
    });
    

    simplemde.codemirror.setCursor({line: 0, ch: 0});
    simplemde.codemirror.focus();

    syncPlayerSlide(current_para.data.start_time);
    player.pause();

}

var pendingSave = false;

function saveScript() {
    if(pendingSave) {
        pendingSave = false;
        document.getElementById('status').innerHTML = 'Saving...'    
        fetch(api_prefix + 'update_script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: env != 'dev' ? sessionStorage.getItem('userId') : 'junyang168@gmail.com',
                item: scriptData.item,
                paragraphs: scriptData.scripts
            })
        })
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').innerHTML = 'Saved'    
                console.log('Paragraph saved successfully:', data);
            })
            .catch(error => {                    
                console.error('Error saving paragraph:', error);
                alert(error)
            });
    }
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
        tr.getElementsByClassName('paragraph')[0].data = para;               
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
            loadFile( 'slide' , item_name , 'json'),
            loadFile( 'script_fixed' , item_name , 'txt'),
            loadFile( 'script' , item_name , 'jsonl')
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
    for(i = 0; i < timelineData.length; i++) {
        item = timelineData[i];
        if(item && item.index) {
            timelineDictionary[item.index] = item;
            item.next_item = i < timelineData.length - 1 && timelineData[i+1] ? timelineData[i+1].index : null;
        }
    }


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
            start_item =  timelineDictionary[timelineItem.next_item];
            para.start_time = calcuateTime( start_item.index , start_item.start_time);
            para.start_timeline = formatTime(para.start_time);

        }
        else {
            para.start_timeline = '00:00:00'
            para.start_time = 0 
        }
        this_timeline = timelineDictionary[ paragraphs[i].index]
        para.end_time = calcuateTime( this_timeline.index, this_timeline.end_time);
        
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
            var slideTextDiv = document.getElementById('slide_text');
            slideTextDiv.innerHTML = slide.text; 
//            simplemde.value(slide.text);
            
            break
        }
    }
}

function syncPlayerSlide(currentTime) {
    setSlideText(currentTime);
    player.currentTime = currentTime;
}

function timeChanged(e) {
    var currentTime = player.currentTime;
    document.getElementById("demo").innerHTML = player.currentTime;
    if (simplemde) {
        current_para = simplemde.element.data;
        if(current_para) {
            if (currentTime < current_para.start_time)
                syncPlayerSlide(current_para.start_time);
            else if(currentTime > current_para.end_time) {
                syncPlayerSlide(current_para.end_time );
                player.pause();
            }
        }
    }
}

async function onLoaded() {
    if(env != 'dev' && !sessionStorage.getItem('userId')) {
        alert('Please sign into Google')
        return
    }


    scriptData = await loadData();

    loadParagraphs(scriptData);

    player = document.getElementById('player'); 
    player.ontimeupdate = function() {timeChanged()};
    player.src = 'data/video/' + scriptData.item + '.mp4';

    
}

window.onload = onLoaded;

