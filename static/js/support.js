console.log('Chat ID:', chatId);
let url = `ws://${window.location.host}/ws/chat/${chatId}/`;

const textarea = document.querySelector('.chat-form textarea');

textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
});



const chatSocket = new WebSocket(url);

chatSocket.onmessage = function(e) {
    let data = JSON.parse(e.data);
    console.log('Data:', data);

    if (data.type === 'chat') {
        let messages = document.getElementById('messages');

        messages.insertAdjacentHTML('beforeend', `
            <div>
                <p>${data.message}</p>
            </div>
        `);

        let notificationSound = document.getElementById('notification-sound');
        notificationSound.play();
    }
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
        e.preventDefault(); // Забороняємо перезавантаження сторінки
        let message = e.target.content.value;
        
        console.log('Sending message:', message);

        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
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