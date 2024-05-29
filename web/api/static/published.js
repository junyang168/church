
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



window.onload = function() {
    showUserProfile();
    var hash = window.location.hash.substr(1); // Get the hash value without the '#'
    var paragraph = document.getElementById(hash); // Select the paragraph
    if (paragraph) { // Check if the paragraph exists
        paragraph.style.color = "red"; // Change the color to red
        if (paragraph) {
            paragraph.style.color = "red";
            paragraph.scrollIntoView();
        }
    }
};
