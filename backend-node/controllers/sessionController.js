const { sessions } = require('../services/sessionService');
const { getConnectionStatus } = require('../services/whatsappService');
const { apiKeys } = require('../services/apiKeyService');

exports.getStatus = async (req, res) => {
    const { userId } = req.params;
    
    try {
        const status = await getConnectionStatus(userId);
        const isConnected = status === 'connected';
        
        res.json({
            userId,
            status,
            isConnected,
            sessionExists: !!sessions[userId]
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.disconnect = async (req, res) => {
    const { userId } = req.params;
    
    try {
        const sock = sessions[userId];
        if (sock) {
            await sock.end();
            delete sessions[userId];
        }
        res.json({ 
            success: true, 
            message: 'Disconnected successfully' 
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getApiKey = async (req, res) => {
    const { userId } = req.params;
    
    const key = Object.keys(apiKeys).find(k => apiKeys[k] === userId);
    
    if (key) {
        res.json({ apiKey: key });
    } else {
        res.status(404).json({ error: 'API key not found' });
    }
};