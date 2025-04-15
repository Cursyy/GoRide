(function (){
    "use strict";

    function updateAvatar(){
        const hatImg = document.getElementById("hat");
        const shirtImg = document.getElementById("shirt");
        const accessoryImg = document.getElementById("accessory");
        const backgroundImg = document.getElementById("background");

        const hatCard = document.querySelector(`.item-card[data-type="hat"][data-id="${window.currentAvatar.hat}"]`);
        const shirtCard = document.querySelector(`.item-card[data-type="shirt"][data-id="${window.currentAvatar.shirt}"]`);
        const accessoryCard = document.querySelector(`.item-card[data-type="accessory"][data-id="${window.currentAvatar.accessory}"]`);
        const backgroundCard = document.querySelector(`.item-card[data-type="background"][data-id="${window.currentAvatar.background}"]`);
        
        if(hatCard){
            hatImg.src = hatCard.getAttribute("data-url");
            hatImg.style.display = "block";
        }
        else{
            hatImg.style.display = "none";
        }

        if(shirtCard){
            shirtImg.src = shirtCard.getAttribute("data-url");
            shirtImg.style.display = "block";
        }
        else{
            shirtImg.style.display = "none";
        }

        if(accessoryCard){
            accessoryImg.src = accessoryCard.getAttribute("data-url");
            accessoryImg.style.display = "block";
        }
        else{
            accessoryImg.style.display = "none";
        }

        if(backgroundCard){
            backgroundImg.src = backgroundCard.getAttribute("data-url");
            backgroundImg.style.display = "block";
        }
        else{
            backgroundImg.style.display = "none";
        }
    }

    function handleAvatarUpdate(data){
        console.log("Avatar handling avatar update: ", data);
        if(!data.avatar){
            console.warn("handleAvatarUpdate: No avatar data");
            return;
        }

        window.currentAvatar = data.avatar;
        updateAvatar();
    }

    if (window.WebSocketManager){
        window.WebSocketManager.register("avatar_update", handleAvatarUpdate);
        console.log("Avatar: Registered avatar_update handler");
    }
    else{
        console.error("Avatar: WebSocketManager not found");
    }

    window.equipItem = function(element){
        const type = element.getAttribute("data-type");
        const id = element.getAttribute("data-id");

        if(window.currentAvatar[type] === id){
            window.currentAvatar[type] = null;
        }
        else{
            window.currentAvatar[type] = id;
        }

        console.log("Equipping:", type, id);
        updateAvatar();

        window.WebSocketManager.sendMessage("avatar_update", {
            hat: window.currentAvatar.hat,
            shirt: window.currentAvatar.shirt,
            accessory: window.currentAvatar.accessory,
            background: window.currentAvatar.background,
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        updateAvatar();
    });
}) ();