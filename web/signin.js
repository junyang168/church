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

function showUserProfile() {
    var userId = sessionStorage.getItem('userId');
    var user_info = document.getElementById("user_info")
    if(userId) {
        user_name = sessionStorage.getItem('user_name')
        if(user_name) {
            user_info.getElementsByTagName("span")[0].innerText = user_name;   
        }

        user_info.getElementsByTagName("img")[0].src = sessionStorage.getItem('picture');
        user_info.style.display = "flex";
        if(env == 'production')
            document.getElementById("g_id_onload").nextElementSibling.style.display = "none";
    }
    else {
        user_info.style.display = "none";
    }

}

async function loadUserInfo(user_id) {
    try {
        url = `${api_prefix}user/${user_id}`
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data =  await response.json();
        sessionStorage.setItem('user_name', data.name);
        return data
    } catch (error) {
        console.error(error);
    }  
    return null    
}


async function onSignIn(googleUser) {
    console.log("Succesfully Singed in!!!");
    const responsePayload = decodeJwtResponse(googleUser.credential);
    if (responsePayload) {
        userId = responsePayload.email
        sessionStorage.setItem('userId', userId);
        sessionStorage.setItem('picture', responsePayload.picture);
                
        console.log("User ID: ", userId);

        onLoaded()
    }
}

async function getUserId() {
    var user_id = env != 'dev' ? sessionStorage.getItem('userId') : 'junyang168@gmail.com'
    var userInfo =  await loadUserInfo(user_id)

    if(!userInfo) {
        alert('You are not authorized to access this site')
        return null
    }

    return user_id
}


async function checkSignin() {
    var main = document.getElementsByTagName('main')[0]
    var msg = document.getElementById("signin_msg");

    var urlParams = new URLSearchParams(window.location.search);
    temp_key =  urlParams.get('key');

    if(temp_key && temp_key == '987986786876874287') {
        sessionStorage.setItem('userId', 'tempacess@holylogos.org')
        sessionStorage.setItem('picture','https://lh3.googleusercontent.com/a/ACg8ocKPLUaez5y6suLdpjEb6453tOtm_AyXXR1JgIJZLW3xeOKRO7aN=s96-c')
    }


    if(  !sessionStorage.getItem('userId')) {

        if(main)
            main.style.display = "none";
        if( msg) 
            msg.style.display = "block";
        else
            alert('Please sign into Google')
        return null;
    }
//    else if (env == 'dev' ) {    
//            sessionStorage.setItem('userId', 'junyang168@gmail.com')
//            sessionStorage.setItem('picture','https://lh3.googleusercontent.com/a/ACg8ocKPLUaez5y6suLdpjEb6453tOtm_AyXXR1JgIJZLW3xeOKRO7aN=s96-c')
//    }

    if(main)
        main.style.display = 'block'
    if(msg) 
        msg.style.display = "none";  

    user_id = await getUserId()
    showUserProfile()    
    return user_id
}
