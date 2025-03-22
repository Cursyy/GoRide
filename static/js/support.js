const textarea = document.querySelector('.chat-form textarea');

textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
});

document.addEventListener("DOMContentLoaded", function() {
    const sound = document.getElementById("notification-sound");

    async function checkMessages() {
        try {
            const response = await fetch("unread/");
            const data = await response.json();

            if (data.new_messages > 0) {
                sound.play();
                alert(`You have ${data.new_messages} unread messages!`);
            }
        } catch (error) {
            console.error("Error checking messages: ", error);
        }
    }

    setInterval(checkMessages, 10000);
});