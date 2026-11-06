const http = require('http');

// Функция генерации данных (аналог нашего sources.py)
function generateBatch(sourceId) {
    const n = Math.floor(Math.random() * (600 - 100 + 1)) + 100; // 100-600
    const batch = [];
    
    for (let i = 0; i < n; i++) {
        const objectId = `src${sourceId}_obj${i}`;
        // Генерируем разные типы данных
        const r = Math.random();
        let value;
        if (r < 0.4) {
            value = Math.floor(Math.random() * 2000) - 1000; // int
        } else if (r < 0.8) {
            value = (Math.random() * 2000 - 1000).toFixed(3); // float
        } else if (r < 0.95) {
            value = Math.random() > 0.5; // boolean
        } else if (r < 0.98) {
            value = "bad_value"; // строка (невалидно)
        } else {
            value = null; // null (невалидно)
        }

        batch.push({
            source_id: sourceId,
            object_id: objectId,
            value: value,
            timestamp: Date.now() / 1000
        });
    }
    return batch;
}

// Создаем HTTP-сервер
const server = http.createServer((req, res) => {
    // Если пришел запрос на /api/data
    if (req.url === '/api/data') {
        // Генерируем данные от всех 4 источников
        let allData = [];
        for (let i = 1; i <= 4; i++) {
            allData = allData.concat(generateBatch(i));
        }
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(allData));
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`[JS Server] Источники телеметрии запущены на http://localhost:${PORT}/api/data`);
});