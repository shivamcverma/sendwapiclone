const express = require('express');
const router = express.Router();

// ✅ Auth check - GET route
router.get('/check', (req, res) => {
    res.json({ 
        status: 'authenticated',
        timestamp: new Date().toISOString()
    });
});

// ✅ Auth check - POST route
router.post('/check', (req, res) => {
    res.json({ 
        status: 'authenticated',
        timestamp: new Date().toISOString()
    });
});

// ✅ Ping - GET route
router.get('/ping', (req, res) => {
    res.json({ 
        status: 'pong',
        timestamp: new Date().toISOString()
    });
});

module.exports = router;