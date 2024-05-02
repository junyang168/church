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
        user_info.getElementsByTagName("img")[0].src = sessionStorage.getItem('picture');
        user_info.style.display = "flex";
        if(env == 'production')
            document.getElementById("g_id_onload").nextElementSibling.style.display = "none";
    }
    else {
        user_info.style.display = "none";
    }

}

function onSignIn(googleUser) {
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
function getUserId() {
    return  user_id = env != 'dev' ? sessionStorage.getItem('userId') : 'junyang168@gmail.com'

}


function checkSignin() {
    if(  env =='production' && !sessionStorage.getItem('userId')) {
        alert('Please sign into Google')
        return null;
    }
    else if (env == 'dev') {    
            sessionStorage.setItem('userId', 'junyang168@gmail.com')
            sessionStorage.setItem('picture','https://lh3.googleusercontent.com/a/ACg8ocKPLUaez5y6suLdpjEb6453tOtm_AyXXR1JgIJZLW3xeOKRO7aN=s96-c')
    }

    user_id = getUserId()
    showUserProfile()    
    return user_id
}
