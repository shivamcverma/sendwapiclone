const fetch = require('node-fetch');

const DJANGO_WEBHOOK_URL = process.env.DJANGO_WEBHOOK_URL || 'http://localhost:8000/api/messaging/webhook/';

async function sendWebhook(endpoint, data) {
    try {
        const url = `${DJANGO_WEBHOOK_URL}${endpoint}`;
        console.log(`📨 Sending webhook to: ${url}`);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        console.log(`✅ Webhook response:`, result);
        return result;
        
    } catch (error) {
        console.error('❌ Webhook failed:', error.message);
        return null;
    }
}

module.exports = { sendWebhook };