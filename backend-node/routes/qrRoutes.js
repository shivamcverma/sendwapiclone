const express = require("express");
const router = express.Router();

const {
    startSession,
    getSessionById,
    getSession,
    getQR,
    waitForQR
} = require("../services/sessionService");

router.post("/start", async (req, res) => {
try {
console.log("========== QR START ==========");
console.log("QR START BODY:", req.body);

const { userId, phoneNumber } = req.body;

if (!userId) {
return res.status(400).json({
success: false,
message: "userId is required"
});
}

if (!phoneNumber) {
return res.status(400).json({
success: false,
message: "phoneNumber is required"
});
}

const number = String(phoneNumber).replace(/\D/g, "");

console.log("USER ID:", userId);
console.log("PHONE:", number);

const session = await startSession(
userId,
number
);

console.log("SESSION CREATED:", session?.sessionId);
console.log("ACTIVE SESSIONS:", Object.keys(
require("../services/sessionService").getAllSessions()
));

let qr = session?.qrImage || null;

if (!qr) {
qr = await waitForQR(userId, 20000);
}

const currentSession = getSession(userId);

console.log("CURRENT SESSION:", currentSession?.sessionId);
console.log("CURRENT SESSIONS:", Object.keys(
require("../services/sessionService").getAllSessions()
));

if (!currentSession) {
return res.status(500).json({
success: false,
message: "Session could not be created"
});
}

return res.json({
success: true,
userId: String(userId),
sessionId: currentSession.sessionId,
phoneNumber: currentSession.phoneNumber,
connected: currentSession.connected,
connectedNumber: currentSession.connectedNumber,
qr: qr || currentSession.qrImage || null
});

} catch (error) {
console.error("QR START ERROR:", error);

return res.status(500).json({
success: false,
message: error.message
});
}
});

router.get("/:sessionId", (req, res) => {
    const sessionId = String(req.params.sessionId);

    console.log("QR STATUS SESSION:", sessionId);

    const {
        getSessionById,
        getQR
    } = require("../services/sessionService");

    const session = getSessionById(sessionId);

    console.log(
        "GET SESSION BY ID:",
        sessionId
    );

    console.log(
        "SESSION FOUND:",
        !!session
    );

    if (!session) {
        return res.status(404).json({
            success: false,
            connected: false,
            qr: null,
            message: "Session not found"
        });
    }

    if (session.connected) {
        return res.json({
            success: true,
            connected: true,
            sessionId: session.sessionId,
            phoneNumber: session.phoneNumber,
            connectedNumber: session.connectedNumber,
            qr: null
        });
    }

    return res.json({
        success: true,
        connected: false,
        sessionId: session.sessionId,
        phoneNumber: session.phoneNumber,
        qr: getQR(session.userId)
    });
});
module.exports = router;