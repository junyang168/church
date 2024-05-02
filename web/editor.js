var scriptData = {}
var player = null;
var permissions = null;
var user_id = null;
var context = null;

async function loadFile(user_id, type, item_name, ext) {
    try {
        url = `${api_prefix}load/${user_id}/${type}/${item_name}/${ext}`
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data =  await response.json();
        return data
    } catch (error) {
        console.error(error);
    }      
}


async function getContext() {

    user_id = getUserId()
    if(!user_id) {
        alert('Please sign into Google')
        return null
    }

    var urlParams = new URLSearchParams(window.location.search);
    item_name =  urlParams.get('i');
    permissions = await loadPermissions(user_id, item_name)

    if(!permissions || !permissions.canRead) {
        alert('You do not have permission to view this item')
        return null
    }


    context =  { user_id: user_id,
            item_name :item_name,
            view_changes: urlParams.get('c') == 'true'
        }

    return context

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

function highlightCurrentPara(current_para) {

    if( permissions && permissions.canWrite && !context.view_changes) 
        return false

    current_para.style.backgroundColor = 'yellow';
    player.play()
    var paras =  document.getElementsByClassName('paragraph')
    for( ta of paras){
        if( ta != current_para && ta.style.backgroundColor == 'yellow' ) {
            ta.style.backgroundColor = 'inherit';
            break;
        }
    }
    return true
}

function turnOnEditor(para_id) {
    current_para = document.getElementById(para_id)
    syncPlayerSlide(current_para.data.start_time);

    if( highlightCurrentPara(current_para) )
        return

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
        "link", "image","quote", "horizontal-rule", "preview", "side-by-side", "fullscreen","|",
        {
            name: "play",
            action: function(editor) {
                para = editor.element.data;
                player.play()

            },
            title: "Play Video",
            className: "fa fa-play", 
          },
          {
            name: "pause",
            action: function(editor) {
                player.pause()

            },
            title: "Pause Video",
            className: "fa fa-pause", 
          },
          {
            name: "Rewind",
            action: function(editor) {
                para = editor.element.data;
                syncPlayerSlide(para.start_time);
                player.play()

            },
            title: "Play from start",
            className: "fa fa-fast-backward", 
          }
  
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

        if(!pendingSaves['scripts']) {
            pendingSaves['scripts'] = true;
            setTimeout(saveScript, saveDelay);
        }
    });
    

    simplemde.codemirror.setCursor({line: 0, ch: 0});
    simplemde.codemirror.focus();

    player.pause();

}

var pendingSaves = {
    slides: false,
    scripts: false
};

function saveScript() {
    for( dataKey in pendingSaves) {
        if(!pendingSaves[dataKey])
            continue;
        pendingSaves[dataKey] = false;
        document.getElementById('status').innerHTML = `Saving ${dataKey}...`
        fetch(api_prefix + 'update_script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: env != 'dev' ? sessionStorage.getItem('userId') : 'junyang168@gmail.com',
                item: scriptData.item,
                type : dataKey,
                data: scriptData[dataKey]
            })
        })
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').innerHTML = 'Saved'    
                console.log( dataKey, ' saved successfully:', data);
            })
            .catch(error => {                    
                console.error('Error saving', dataKey, error);
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


function matchCaret(caret, e, byIndx) {
    if( byIndx)
        return caret.data.index == e
    else
        return caret == e
}

function setBookMark( e, byIndx ) {
    if(!e) 
        return null;
    sc = document.getElementById('sc');
    var carets =  document.getElementsByClassName('caret')
    var matachedCaret = null
    for( var caret of carets){
        icon = caret.getElementsByTagName('i').length
        matched  = matchCaret(caret, e, byIndx)
        if( icon == 0 && matched) {
            matachedCaret = caret
            caret.innerHTML = '<i class="fa-solid fa-caret-right"></i>';
            caret.nextElementSibling.style.color = 'black';
            caret.nextElementSibling.style.fontWeight = 'bold';
        }
        else if (icon > 0 && !matched) {
            caret.innerHTML = '';   
            caret.nextElementSibling.style.color = 'grey';
            caret.nextElementSibling.style.fontWeight = 'lighter';
        }
    }
    return matachedCaret
}

async function loadBookark() {
    try {
        url =  api_prefix + `bookmark/${context.user_id}/${context.item_name}`    
        const response = await fetch(url );
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        bookmark =  await response.json();
        bm = setBookMark(bookmark.index, true)
//        if(bm)
//            bm.scrollIntoView();
        
    } catch (error) {
        console.error(error);
    }      
}

async function updateBookmark(caret, byIndx) {
    setBookMark(caret, byIndx)    
    try {
        var index = byIndx?caret:caret.data.index;
        url =  api_prefix + `bookmark/${context.user_id}/${context.item_name}/${index}`    
        const response = await fetch(url, { method: 'PUT'} );
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        data =  await response.json();
        
    } catch (error) {
        console.error(error);
    }      
}

async function onRowClicked(e) {

    if(simplemde) {
        ta = simplemde.element
        if(sameRow(e.target, ta))
            return;
    }
    para_id = getTextAreInRow(e.target).id;

    turnOnEditor(para_id);

    if( e.target.classList.contains('caret') )
        updateBookmark(e.target, false);
    else if (e.target.classList.contains('timeline')) 
        updateBookmark(e.target.previousElementSibling, false);

}

function loadParagraphs(scriptData) {

    sc = document.getElementById('sc');
    scriptData.scripts.forEach(function(para) {
        var tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="caret" width='20'></td>
            <td class="timeline" width='50'>${para.start_timeline}</td>
            <td><textarea id="${para.index}" readonly class="paragraph">${para.text}</textarea></td>`;
        tr.onclick = onRowClicked 
        sc.appendChild(tr);
        tr.getElementsByClassName('paragraph')[0].data = para;               
        tr.getElementsByClassName('caret')[0].data = para;               
    })

    var paras =  document.getElementsByClassName('paragraph')
    for( ta of paras){
        ta.style.height = ta.scrollHeight + 'px';
    }
}

function loadParagraphChanges(scriptChanges) {
    var sc_changes = document.getElementById('sc');

    scriptChanges.forEach(function(para) {
        text = para.text
        text = text.replace(/\n/g,'<br/>')
        text = text.replace(/<->/g,'<span class="change_red">')
        text = text.replace(/<\+>/g,'<span class="change_green">')
        text = text.replace(/<\/>/g,'</span>')
        var tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="timeline" width='50'>${para.start_timeline}</td>
            <td><div id="c_${para.index}" class="paragraph">${text}</div></td>`;
        tr.onclick = onRowClicked 
        sc_changes.appendChild(tr);
        tr.getElementsByClassName('paragraph')[0].data = para;               
    })

    var paras =  document.getElementsByClassName('paragraph')
    var viewportWidth = window.innerWidth;
    for( ta of paras){
        ta.style.width = viewportWidth - 700 + 'px';
    }

}


async function loadPermissions(user_id, item) {
    try {
        url = `${api_prefix}permissions/${user_id}/${item}`
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(error);
    }      
}

async function loadData(context) {
    var user_id = context.user_id
    var item_name = context.item_name
    var view_changes = context.view_changes

    const [slide_text, paragraphs, timeline ] = await Promise.all([ 
            loadFile(user_id, 'slide' , item_name , 'json'),
            loadScript(user_id , item_name , view_changes),
            loadFile(user_id,  'script' , item_name , 'jsonl')
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

    return {
        slides: slideData,
        scripts: paragraphs,
        item:item_name            
    }    
}





function setSlideText(currentTime) {
    for(i = 0; i < scriptData.slides.length; i++) {
        slide = scriptData.slides[i]; 
        if ( currentTime > slide.time && currentTime < (i < scriptData.slides.length -1 ? scriptData.slides[i+1].time: 9999999999)) {
            var slideTextArea = document.getElementById('slide_text');
            slideTextArea.value = slide.text;
            slideTextArea.data = slide;            
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
    else {
        setSlideText(currentTime);
        var paras =  document.getElementsByClassName('paragraph')
        for( ta of paras){
            para = ta.data
            if( para.end_time > currentTime && para.start_time <= currentTime) {
                if(ta.style.backgroundColor != 'yellow') {
                    highlightCurrentPara(ta);
                }                
                break;
            }
        }
    
    }
}





async function loadScript(user_id, item, with_changes) {
    try {
        changes = with_changes? 'changes' : 'no_changes'
        url = `${api_prefix}sermon/${user_id}/${item}/${changes}`
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(error);
    }      
}


function onViewChanges(e) {    

    window.location.href = `sermon.html?i=${context.item_name}&c=${!context.view_changes}`;
}

function setViewChangeButton(view_changes_btn) {
    var icon = view_changes_btn.getElementsByTagName('i')[0]
    var label = view_changes_btn.getElementsByTagName('label')[0]
    if(context.view_changes) {
        icon.classList.remove('fa-check')
        icon.classList.add('fa-pen')
        label.innerText = 'Edit'
    }
    else {
        icon.classList.remove('fa-pen')
        icon.classList.add('fa-check')
        label.innerText = 'View Changes'
    }  
}



function setAssignButton(assign_btn) {
    var icon = assign_btn.getElementsByTagName('i')[0]
    var label = assign_btn.getElementsByTagName('label')[0]
    if(permissions && permissions.canAssign) 
        label.innerText = '認領'
    else if(permissions && permissions.canUnassign) 
        label.innerText = '取消認領'
    else
        assign_btn.style.display = 'none'
}   

async function assign_item(action) {
    try {
        url = `${api_prefix}assign`
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: context.user_id,
                item: context.item_name,
                action: action
            })

        })
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        permissions =  await response.json();
        location.reload();        
    
    } catch (error) {
        console.error(error);
    }      
}


async function wireup_buttons() {
    var view_changes_btn = document.getElementById('view_changes_btn');
    view_changes_btn.addEventListener('click', onViewChanges);
    setViewChangeButton(view_changes_btn);
    
    document.getElementById('home_btn').addEventListener('click', function() {
        window.location.href = 'index.html';
    }
    );


    var assign_btn = document.getElementById('assign_btn');
    setAssignButton(assign_btn);
    assign_btn.addEventListener('click', function() {
         assign_item(permissions.canAssign? 'assign' : 'unassign')        
    }
    );

}

async function onLoaded() {

    if(!checkSignin())
        return;

    var context = await getContext();
    if(!context)
        return

    wireup_buttons();


    scriptData = await loadData(context);

    if(context.view_changes)
        loadParagraphChanges(scriptData.scripts);
    else
        loadParagraphs(scriptData);

    player = document.getElementById('player'); 
    player.ontimeupdate = function() {timeChanged()};
    player.src = 'data/video/' + scriptData.item + '.mp4';


    var slideTextArea = document.getElementById('slide_text');
    slideTextArea.readOnly = !(permissions && permissions.canWrite);

    slideTextArea.onchange = function() {
        slideTextArea = document.getElementById('slide_text');
        var slide = slideTextArea.data;
        slide.text = slideTextArea.value;
        if(!pendingSaves['slides']) {
            pendingSaves['slides'] = true;
            setTimeout(saveScript, saveDelay);
        }

    }

    loadBookark();

    
}

window.onload = onLoaded;

