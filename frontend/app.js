document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const summarizeButton = document.getElementById('summarize-button');
    const loading = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const resultText = document.getElementById('result-text');
    const fileLabel = document.getElementById('file-label');
    const numRowsInput = document.getElementById('num-rows-input');
    const conclusionText = document.getElementById('conclusion-text');
    const chartCanvas = document.createElement('canvas');
    chartCanvas.id = 'vote-chart';
    resultDiv.appendChild(chartCanvas);

    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            summarizeButton.classList.remove('hidden');
            fileLabel.textContent = "📂 " + file.name;
        }
    });

    summarizeButton.addEventListener('click', () => {
        if (fileInput.files.length === 0) {
            alert('Por favor, selecciona un archivo.');
            return;
        }

        const file = fileInput.files[0];
        const numRows = numRowsInput.value || 10;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('num_rows', numRows);

        loading.classList.remove('hidden');
        resultDiv.classList.add('hidden');

        fetch('http://127.0.0.1:5000/summarize-file', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            loading.classList.add('hidden');

            if (data.error) {
                resultText.textContent = `❌ Error: ${data.error}`;
                resultDiv.classList.remove('hidden');
            } else if (data.votos_luisa !== undefined && data.votos_noboa !== undefined && data.votos_nulo !== undefined) {
                resultText.textContent = `Votos Luisa: ${data.votos_luisa}, Votos Noboa: ${data.votos_noboa}, Votos Nulo: ${data.votos_nulo}`;
                resultDiv.classList.remove('hidden');

                conclusionText.textContent = data.conclusion;

                const ctx = chartCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Votos Luisa', 'Votos Noboa', 'Votos Nulo'],
                        datasets: [{
                            label: 'Conteo de Votos',
                            data: [data.votos_luisa, data.votos_noboa, data.votos_nulo],
                            backgroundColor: [
                                'rgba(56, 99, 188, 0.2)',  // Azul para Luisa
                                'rgba(172, 34, 214, 0.2)', // Morado para Noboa
                                'rgba(75, 192, 192, 0.2)'  // Verde para Nulo
                            ],
                            borderColor: [
                                'rgb(56, 100, 188)',       // Azul para Luisa
                                'rgb(172, 34, 214)',       // Morado para Noboa
                                'rgba(75, 192, 192, 1)'    // Verde para Nulo
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            } else {
                resultText.textContent = '❌ Error: Respuesta inesperada del servidor.';
                resultDiv.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loading.classList.add('hidden');
            resultText.textContent = '❌ Error: No se pudo conectar al servidor.';
            resultDiv.classList.remove('hidden');
        });
    });

    const sendQuestion = async (question) => {
        const response = await fetch('http://127.0.0.1:5000/ask-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();
        return data.answer;
    };

    const addMessage = (message, isUser) => {
        const messageElement = document.createElement('div');
        
        if (isUser) {
            // Pregunta del usuario con formato
            messageElement.innerHTML = `<strong>Pregunta del usuario:</strong> ${message}`;
        } else {
            // Respuesta del chatbot con formato
            messageElement.innerHTML = `<strong>Respuesta del chat bot:</strong> ${message}`;
        }

        messageElement.classList.add(isUser ? 'user-message' : 'bot-message');
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    sendButton.addEventListener('click', async () => {
        const question = chatInput.value.trim();
        if (question) {
            addMessage(question, true);
            chatInput.value = '';

            try {
                const answer = await sendQuestion(question);
                addMessage(answer, false);
            } catch (error) {
                console.error('Error:', error);
                addMessage("❌ Error: No se pudo obtener una respuesta del servidor.", false);
            }
        }
    });
});