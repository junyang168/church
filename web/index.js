function decodeToken(token) {
    try {
        const decoded = jwt_decode(token);
        console.log(decoded);
        return decoded;
    } catch (error) {
        console.error("Invalid token", error);
        return null;
    }
}

function validateTokenClaims(decodedToken) {
    const currentTimestamp = Math.floor(Date.now() / 1000); // Current time in seconds

    // Check if the token is expired
    if (decodedToken.exp < currentTimestamp) {
        console.error("Token has expired");
        return false;
    }
    // Additional claim checks
    // For example, validate issuer or audience
    if (decodedToken.iss !== 'https://accounts.google.com') {
        console.error("Invalid issuer");
        return false;
    }

    return true; // Token is valid
}

function decodeJwtResponse(token) {
    const decoded = decodeToken(token);
    if (decoded && validateTokenClaims(decoded)) {
        console.log("Token is valid and active.");
        // Proceed with application logic, e.g., store the token for session management
        return decoded
    } else {
        console.log("Token is invalid or inactive.");
        // Handle invalid token, e.g., redirect to login
        return null
    }
}

function onSignIn(googleUser) {
    console.log("Succesfully Singed in!!!");
    const responsePayload = decodeJwtResponse(googleUser.credential);
    if (responsePayload) {
        userId = responsePayload.email
        sessionStorage.setItem('userId', userId);
        onLoaded()
    }
}


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

   if(env != 'dev' && !sessionStorage.getItem('userId')) {
        alert('Please sign into Google')
        return
    }
    
    user_id = env != 'dev' ? sessionStorage.getItem('userId') : 'junyang168@gmail.com'

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
            {title:"標題", width:500, formatter:"link", formatterParams:function(cell){
                var sermon = cell.getRow().getData();
                url = sermon.status != 'in development' ?  `sermon.html?i=${encodeURIComponent(sermon.item)}` : '#'
                return {
                    label: sermon.title, 
                    url: url
                };
            }},            
            {title:"發布日期", field:"deliver_date", sorter:"string", width:150},
            {title:"認領人", field:"assigned_to_name", sorter:"string", width:100},
            {title:"更新人", field:"author_name", sorter:"string", width:100},
            {title:"更改日期", field:"last_updated", sorter:"string", width:150},
            {title:"Status", field:"status", sorter:"string"}
        ]
    });
    
}

window.onload = onLoaded;

