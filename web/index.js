

async function getSermons(user_id) {
    try {
        url = `${api_prefix}sermons/${user_id}`
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(error);
    }      
}


async function onLoaded() {

    user_id = await checkSignin();
    if(!user_id) return;

    sermons = await getSermons(user_id)

    document.getElementById('total_number').innerText = sermons.length

    var table = new Tabulator("#sermons-table", {
        data:sermons, //assign data to table
        columns:[
            {title:"", field:"type", width:30, formatter:function(cell, formatterParams){
                var value = cell.getRow().getData().type;
                 if(value == 'audio'){
                    return "<i class='fa-solid fa-music'></i>";
                 }else{
                    return "<i class='fa-solid fa-video'></i>";
                 }
             }},          
            {title:"標題", width:350, formatter:"link", formatterParams:function(cell){
                var sermon = cell.getRow().getData();
                url = sermon.status != 'in development' ?  `sermon.html?v=0407&i=${encodeURIComponent(sermon.item)}` : '#'
                return {
                    label: sermon.title, 
                    url: url
                };
            }},            
            {title:"發布日期", field:"deliver_date", sorter:"string", width:150},
            {title:"認領人", field:"assigned_to_name", sorter:"string", width:100},
            {title:"認領日期", field:"assigned_to_date", sorter:"string", width:100},
            {title:"完成日期", field:"published_date", sorter:"string", width:100},
            {title:"更新人", field:"author_name", sorter:"string", width:100},
            {title:"更改日期", field:"last_updated", sorter:"string", width:150},
            {title:"Status", field:"status", sorter:"string"}
        ]
    });
    
}

window.onload = onLoaded;

