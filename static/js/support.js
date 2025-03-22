const textarea = document.querySelector('.chat-form textarea');

textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
});

let url = `ws://${window.location.host}/ws/socket-server/`;

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

let form = document.getElementById('form');
form.addEventListener('submit', (e) => {
    e.preventDefault();
    let message = e.target.message.value;

    chatSocket.send(JSON.stringify({
        'message': message
    }));

    form.reset();
});