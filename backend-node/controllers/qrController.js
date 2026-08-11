const {
    startSession,
    getSession,
    waitForQR
} = require("../services/sessionService");
console.log(
    "QR CONTROLLER LOADED"
);
exports.generateQR = async (req, res) => {
    try {
        const userId = req.body.userId;
        const phoneNumber = req.body.phoneNumber;
        console.log(
        "GENERATE QR CALLED:",
        req.body
        );
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

        /*
         * Check existing session
         */
        const existingSession =
            getSession(userId);

        if (existingSession) {
            return res.json({
                success: true,
                connected:
                    existingSession.connected,
                sessionId:
                    existingSession.sessionId,
                phoneNumber:
                    existingSession.phoneNumber,
                qr:
                    existingSession.qrImage || null,
                connectedNumber:
                    existingSession.connectedNumber || null
            });
        }

        /*
         * Start new WhatsApp session
         */
        const session =
            await startSession(
                userId,
                phoneNumber
            );

        if (!session) {
            return res.status(500).json({
                success: false,
                message: "WhatsApp session could not be created"
            });
        }

        /*
         * QR ke liye wait karo
         */
        const qr =
            await waitForQR(
                userId,
                15000
            );

        /*
         * Session dobara check karo
         */
        const currentSession =
            getSession(userId);

        if (!currentSession) {
            return res.status(500).json({
                success: false,
                message: "WhatsApp session unavailable"
            });
        }

        return res.json({
            success: true,
            connected:
                currentSession.connected,
            sessionId:
                currentSession.sessionId,
            phoneNumber:
                currentSession.phoneNumber,
            qr:
                qr ||
                currentSession.qrImage ||
                null,
            connectedNumber:
                currentSession.connectedNumber ||
                null
        });

    } catch (error) {
        console.error(
            "Generate QR Error:",
            error
        );

        return res.status(500).json({
            success: false,
            message: "Failed to generate QR",
            error: error.message
        });
    }
};