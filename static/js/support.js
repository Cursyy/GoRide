console.log('Chat ID:', chatId);
let url = `ws://${window.location.host}/ws/chat/${chatId}/`;

const textarea = document.querySelector('.chat-form textarea');

textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
});
document.addEventListener('DOMContentLoaded', scrollToBottom);

function scrollToBottom() {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}



const chatSocket = new WebSocket(url);

chatSocket.onmessage = function(e) {
    let data = JSON.parse(e.data);
    console.log('Data:', data);

    if (data.type === 'chat') {
        const messageHtml = `
            <div class="mb-3">
                <strong style="color: #0E6655;">${data.username}:</strong>
                <p>${data.message}</p>
                <small class="text-muted">${data.created_at}</small>
            </div>
        `;
        addNewMessage(messageHtml)
        let notificationSound = document.getElementById('notification-sound');
        notificationSound.play();
    }
}


function addNewMessage(messageHtml) {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
    scrollToBottom();
}


chatSocket.onerror = function(e) {
    console.error('WebSocket error:', e);
};
chatSocket.onopen = function(e) {
    console.log('WebSocket connection established');
};
chatSocket.onclose = function(e) {
    console.log('WebSocket connection closed');
};
let form = document.getElementById('form');
if (form) {
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        let message = e.target.content.value;
        
        console.log('Sending message:', message);

        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'chat_id': chatId,
                'message': message
            }));
            form.reset();
        } else {
            console.error('WebSocket connection is not open.');
        }
    });
} else {
    console.error('Form not found.');
}
