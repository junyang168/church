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
        return '[]'
    }      
}


async function getContext() {

    user_id = await getUserId()
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
            user_name: sessionStorage.getItem('user_name'),
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
var cropper_paragraph = null;
var cropper_toolbar = null;

function onKeyup(cm,event) {
    var pos = cm.getCursor();
    var lineCount = cm.lineCount();
    console.log('currentPos:',currentPos)
    console.log('Pos:',pos)

    direction = null
    if(event.key === 'ArrowDown' && pos.line === lineCount - 1 && currentPos && currentPos.ch == pos.ch) 
        direction = 'Next'
    else if (event.key === 'ArrowUp' && pos.line === 0 && currentPos && currentPos.ch == pos.ch)
        direction = 'Prev'

    if(direction) {
        ta = cm.getTextArea()
        var parent = ta.parentNode.parentNode;
        var nextRow = direction=='Next'? parent.nextElementSibling : parent.previousElementSibling
        if(nextRow ) {
            nextPara = nextRow.getElementsByClassName('paragraph')[0]
            turnOnEditor(nextPara)
        }

    }

}    

function onKeydown(cm,event) {
    var pos = cm.getCursor();
    var lineCount = cm.lineCount();
    currentPos = null   
    if(event.key === 'ArrowDown' && pos.line === lineCount - 1 || event.key === 'ArrowUp' && pos.line === 0) 
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

function getImageInfo(markdownString) {
    let regex = /!\[(.*?)\]\((.*?)\)/;
    let match = markdownString.match(regex);
    
    if (match) {
        let title = match[1];
        let url = match[2];

        sec = title.split(' ')
        if(sec.length > 1) {
            var imgInfo =  {x: parseFloat(sec[0]), y:parseFloat(sec[1]), width:parseFloat(sec[2]), height:parseFloat(sec[3]), url:url} 
            imgInfo.rotate = sec.length > 4? parseFloat(sec[4]) : 0;
            return imgInfo;
        }
        else
            return {url:url}
    
    }
    return null
}

function removeEditor() {
    if(!simplemde)
        return;
    if (simplemde instanceof SimpleMDE) {
        var currTA = simplemde.element
        currTA.previousElementSibling.style.display = 'block';
        simplemde.toTextArea();
        currTA.parentNode.removeChild(currTA);        
    } else if (simplemde instanceof Cropper)  {
        var cbox = simplemde.getData()
        setSlideImageStyle(cropper_paragraph, cbox);
        cropper_toolbar.parentNode.removeChild(cropper_toolbar);
        simplemde.destroy();

    }
    simplemde = null;
}

function turnOnEditor(current_para) {
    syncPlayerSlide(current_para.data.start_time);

    if( highlightCurrentPara(current_para) )
        return

    player.pause();

    removeEditor();

    if(current_para.data.type == 'comment') {
        var imgInfo = getImageInfo(current_para.data.text)
        if(imgInfo) {
            var toolbar = document.createElement('div');
            toolbar.className = 'editor-toolbar';
            toolbar.style.display = 'flex';
            var anchor = document.createElement('a');
            anchor.title = 'Crop Image';
            anchor.className = 'fa-solid fa-cut';
            anchor.onclick = function(e) {   
                cbox = simplemde.getData()
                image_text = `![${cbox.x} ${cbox.y} ${cbox.width} ${cbox.height} ${cbox.rotate}](${imgInfo.url})`
                current_para.data.text = image_text
                console.log('image_text:', image_text);

                removeEditor();


                if(!pendingSaves['scripts']) {
                    pendingSaves['scripts'] = true;
                    setTimeout(saveScript, saveDelay);
                }

        
            }
            toolbar.appendChild(anchor);

            if(env == 'dev') {
                var sliderContainer = document.createElement('div');
                sliderContainer.className = 'slidecontainer';
                var rotate = imgInfo.rotate? imgInfo.rotate : 0 
                sliderContainer.innerHTML = `
                <span>-30&#176;</span><input type="range" min="-30" max="30" value="${rotate}" id="myRange"><span>30&#176;</span>
                <span>Rotate: <span class="slider_value"></span></span> `               
                toolbar.appendChild(sliderContainer);

                var slider = sliderContainer.getElementsByTagName("input")[0];
                var output = sliderContainer.getElementsByClassName("slider_value")[0];
                output.innerHTML = rotate + '&#176;'; // Display the default slider value
                
                // Update the current slider value (each time you drag the slider handle)
                slider.oninput = function() {
                    simplemde.rotateTo(slider.value);
                    output.innerHTML = this.value + '&#176;';
                } 
            }
    
    
            current_para.parentNode.insertBefore(toolbar, current_para);
            var img = current_para.getElementsByTagName('img')[0]
            var imgContainer = img.parentNode;
            imgContainer.style.width = 'auto';
            imgContainer.style.height = 'auto';
            var imgstyle = img.style;
            imgstyle.maxWidth = '100%';
            imgstyle.width = 'auto';
            imgstyle.height = 'auto';
            
            simplemde = new Cropper(img, {
                zoomable:false,
                data: imgInfo,
                autoCrop: true
            });
            cropper_toolbar = toolbar;
            cropper_paragraph = current_para;
            return
        }
    }

    var textarea = document.createElement('textarea');
    textarea.className = 'paragraph_textarea';
    textarea.style.width = '100%';
    textarea.style.height = '200px';
    textarea.value = current_para.data.text;
    textarea.data = current_para.data;
    
    current_para.parentNode.insertBefore(textarea, current_para.nextSibling);
    current_para.style.display = 'none';

    simplemde = new SimpleMDE({ 
        toolbar: [
        {
            name: "Question",
            action: SimpleMDE.toggleItalic,
            className: "fa-solid fa-question",
            title: "Question (Ctrl+I)",
        },        
        "strikethrough", 
        {
            name: "undo",
            action: function(editor) {
                editor.codemirror.undo();
            },
            className: "fa fa-undo", 
            title: "Undo",
        },        
        "bold", "link", "image","quote", "horizontal-rule", "preview", "side-by-side", "fullscreen",
        {
            name: "Remove Paragraph",
            action: remove_paragraph,
            title: "Remove Paragraph",
            className: "fa-solid fa-trash", 
          },
        
        "|",
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
          },
          "|",
          {
            name: "Import Slide Image",
            action: load_slide_image,
            title: "Capture Slide Image",
            className: "fa fa-camera", 
          },
          {
            name: "Import Slide Text",
            action: load_slide_text,
            title: "Capture Slide Text",
            className: "fa fa-font", 
          }  
    ],
    status: false,
        element: textarea , 
    });
    simplemde.codemirror.on('keydown', onKeydown);         
    simplemde.codemirror.on('keyup', onKeyup);         
    simplemde.codemirror.on('change', function() {
        var updatedContent = simplemde.value();

        var para = simplemde.element.data;
        para.text = updatedContent;
        simplemde.element.previousElementSibling.innerHTML = marked.parse(updatedContent);



        if(!pendingSaves['scripts']) {
            pendingSaves['scripts'] = true;
            setTimeout(saveScript, saveDelay);
        }
    });
    

    simplemde.codemirror.setCursor({line: 0, ch: 0});
    simplemde.codemirror.focus();


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
    ta = getTextAreInRow(e.target);

    turnOnEditor(ta);

    if( e.target.classList.contains('caret') )
        updateBookmark(e.target, false);
    else if (e.target.classList.contains('timeline')) 
        updateBookmark(e.target.previousElementSibling, false);

}

function remove_paragraph() {
    if(!confirm('Are you sure you want to remove this paragraph?'))
        return;

    para = simplemde.element.data;
    scriptData.scripts.splice(para.s_index, 1);
    loadParagraphs(scriptData);
    simplemde.toTextArea();
    simplemde = null;
    if(!pendingSaves['scripts']) {
        pendingSaves['scripts'] = true;
        setTimeout(saveScript, saveDelay);
    }
}

async function load_slide_text() {
    para = simplemde.element.data;
    if(para.type != 'comment') {
        createCommentPara(para)
    }
    
    side_text = await extract_slide_text();

    simplemde.value( slide.text);

}

async function load_slide_image() {
    para = simplemde.element.data;
    if(para.type != 'comment') {
        createCommentPara(para)
    }
    
    player.pause()
    var currentTimeMs = Math.round(player.currentTime * 1000);
    url =  api_prefix + `slide_image/${context.user_id}/${context.item_name}/${currentTimeMs}`    
    const response = await fetch(url );    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    slide = await response.json();

    var cm = simplemde.codemirror;
    cm.replaceSelection(`![image](${encodeURIComponent(slide.image_url)})`);
    cm.focus();

     
}


function createCommentPara(para, text='') {
    comment_para = insertComment(para, text);
    loadParagraphs(scriptData);
    sc = document.getElementById('sc');
    var carets =  sc.getElementsByClassName('caret')
    for( var caret of carets){
        if(caret.data.s_index == comment_para.s_index) {
            ta = getTextAreInRow(caret);
            turnOnEditor(ta);        
            break;
        }
    }

}

function onCommentClicked(e) {
    createCommentPara(e.parentNode.data);
}

function resetScriptIndex() {
    for(i = 0; i < scriptData.scripts.length; i++) {
        scriptData.scripts[i].s_index = i;
    }    
}

function insertComment(para, para_text) {
    if(para.type == 'comment')
        return para;
    comment_data = { text:para_text, type:'comment', user_id:context.user_id, user_name:context.user_name, index:para.index}
    scriptData.scripts.splice(para.s_index, 0, comment_data);
    return comment_data
}

function renderCommentImage(para) {
    if( permissions && permissions.canWrite && !context.view_changes) 
        return `<img ${para.type !='comment'? 'class="chat-icon"':''}  src="images/icons8-comment-50.png" onclick="onCommentClicked(this)"></img>`
    else
        return ''
}

function loadParagraphs(scriptData) {
    resetScriptIndex();

    sc = document.getElementById('sc');
    sc.innerHTML = '';
    scriptData.scripts.forEach(function(para) {
        var tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="caret" width='20'>${renderCommentImage(para)}</td>
            <td class="timeline" width='50'>${para.type =='comment'? para.user_name:para.start_timeline}</td>
            <td><div class="paragraph">${marked.parse(para.text.trim())}</div></td>`;
        tr.ondblclick = onRowClicked 
        sc.appendChild(tr);
        paragraph = tr.getElementsByClassName('paragraph')[0]
        paragraph.data = para;               
        tr.getElementsByClassName('caret')[0].data = para;   

        if(para.type == 'comment' && para.text.trim().startsWith('![')) {
            var imageInfo = getImageInfo(para.text)
            if(imageInfo) {
               setSlideImageStyle(paragraph, imageInfo);
            }
        }
 
    })

}

function setSlideImageStyle(paragraph, imageInfo) {
    if (!('width' in imageInfo)) 
        return;

    var image_container = paragraph.getElementsByTagName('p')[0];
    const slide_image_width = paragraph.offsetWidth - 70;
    image_container.style.width = slide_image_width + 'px';
    image_container.style.height = slide_image_width * imageInfo.height / imageInfo.width + 'px';
    image_container.style.overflow = 'hidden';
    var img_width = slide_image_width / imageInfo.width * 1920;
    var img_height = img_width * 1080 / 1920;
    var img = image_container.getElementsByTagName('img')[0];
    var style = img.style;
    style.display = 'block';
    style.width = img_width + 'px';
    style.height = img_height + 'px';
    style.minWidth = '0px';
    style.minHeight = '0px';
    style.maxWidth = 'none';
    style.maxHeight = 'none';
    style.transform = `translateX(-${imageInfo.x / 1920 * img_width}px) translateY(-${imageInfo.y / 1080 * img_height}px)`;
    if(imageInfo.rotate != 0) {
        style.transform += ` rotate(${imageInfo.rotate}deg)`;
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

    const [slide_text, sermon, timeline_text ] = await Promise.all([ 
            loadFile(user_id, 'slide' , item_name , 'json'),
            loadScript(user_id , item_name , view_changes),
            loadFile(user_id,  'script' , item_name , 'json')
             ])
    var slideData = JSON.parse(slide_text);
    var timelineData = JSON.parse(timeline_text).entries;
    
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
        header: sermon.header,
        scripts: sermon.script,
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
    if(currentTime === null || currentTime === undefined)
        return;
    setSlideText(currentTime);
    player.currentTime = currentTime;
}

function timeChanged(e) {
    var currentTime = player.currentTime;
    document.getElementById("demo").innerHTML = player.currentTime;
    if (simplemde) {
        current_para = simplemde.element.data;
        if(current_para && current_para.type != 'comment') {
            if (currentTime < current_para.start_time)
                syncPlayerSlide(current_para.start_time);
            else if(currentTime > current_para.end_time) {
                syncPlayerSlide(current_para.end_time );
                player.pause();
            }
            else
                setSlideText(currentTime);
        }
    }
    else {
        setSlideText(currentTime);
        var paras =  document.getElementsByClassName('paragraph')
        for( ta of paras){
            para = ta.data
            if( para.type != 'comment' && para.end_time > currentTime && para.start_time <= currentTime) {
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
    var img = view_changes_btn.getElementsByTagName('img')[0]
    var label = view_changes_btn.getElementsByTagName('label')[0]
    if(context.view_changes) {
        img.src = 'images/icons8-edit-30.png'
        label.innerText = '編輯'
    }
    else {
        img.src = 'images/icons8-change-24.png'
        label.innerText = 'View Changes'
    }  
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

function setPublishButton(publish_btn) {    
    if(permissions && permissions.canPublish) 
        publish_btn.style.display = 'block'
    else
        publish_btn.style.display = 'none'
}

async function publish_item() {
    try {
        url = `${api_prefix}publish/${context.user_id}/${context.item_name}`
        const response = await fetch(url, { method: 'PUT' })
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        resp =  await response.json();
        alert(resp.message)
        location.reload();
    
    } catch (error) {
        console.error(error);
    }      
}

async function extract_slide_text() {
    spinner = document.getElementById('spinner-container')
    spinner.style.display = 'flex'
    
    player.pause()
    var currentTimeMs = Math.round(player.currentTime * 1000);
    url =  api_prefix + `slide_text/${context.user_id}/${context.item_name}/${currentTimeMs}`    
    const response = await fetch(url );    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    slide = await response.json();
    spinner.style.display = 'none'
    return slide.text

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

    var publish_btn = document.getElementById('publish_btn');
    setPublishButton(publish_btn);
    publish_btn.addEventListener('click', function() {
         publish_item()        
    }
    );

    var view_finished_btn = document.getElementById('view_finished_btn');
    view_finished_btn.addEventListener('click', function() {
        window.open(`public/${context.item_name}`, '_blank');
    }
    );
    if(!permissions || !permissions.canViewPublished) 
        view_finished_btn.style.display = 'none'

     var extract_text_btn = document.getElementById('extract_text_btn');
        extract_text_btn.addEventListener('click',async function() {
            slide_text = await extract_slide_text();
            var slideTextArea = document.getElementById('slide_text');
            slideTextArea.value = slide_text;
        }
    );  

}

async function onLoaded() {
    var user_id = await checkSignin()

    if(!user_id )
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

    if(scriptData.header.type=='audio') {
        player = document.getElementById('player_audio'); 
        player.style.display = 'block';
        player.src = 'video/' + scriptData.item + '.mp3';
        document.getElementById('player').style.display = 'none';
    }
    else 
    {
        player = document.getElementById('player'); 
        player.src = 'video/' + scriptData.item + '.mp4';
    }
    player.ontimeupdate = function() {timeChanged()};

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

