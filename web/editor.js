function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Don't send this directly to your backend!
    console.log('Full Name: ' + profile.getName());
    console.log('Given Name: ' + profile.getGivenName());
    console.log('Family Name: ' + profile.getFamilyName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This email is retrievable only if the email scope is included in the authorization.

    // The ID token you need to pass to your backend:
    var id_token = googleUser.getAuthResponse().id_token;
    console.log("ID Token: " + id_token);
}


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

var simplemde

async function loadData() {
    simplemde = new SimpleMDE({ element: document.getElementById("slide_textarea") });

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


    var scriptParagraphs = script_text.split('\n\n');
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

    scriptData = await loadData();
    player = document.getElementById('player'); 
    player.ontimeupdate = function() {timeChanged()};
    player.src = 'data/video/' + scriptData.item + '.mp4';

    var sc = document.getElementById('sc');
    scriptData.scripts.forEach(function(para) {
        var div = document.createElement('div');
        div.innerHTML ='<div class="timeline" >'+ para.start_timeline + '</div><div style="display:table-cell">' + para.text + "</div>";
        div.style.display = 'block';
        div.style.margin = '10px';
        div.style.cursor = 'pointer';
        div.style.display = 'table-row';
        div.data = para
        div.onclick = function(e) {
            para = e.target.parentNode.data;
            player = document.getElementById('player');
            player.currentTime =  para.start_time;
            player.play();
        }
        sc.appendChild(div);
    });
    setSlideText(0);


}

window.onload = onLoaded;

