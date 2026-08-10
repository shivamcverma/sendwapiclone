const express = require("express");
const crypto = require("crypto");

const router = express.Router();

const {
    startSession,
    getSession,
    getQR,
    waitForQR
} = require("../services/sessionService");


function generateSessionId() {
    return "wa_" + crypto
        .randomBytes(8)
        .toString("hex");
}


router.post("/start", async (req, res) => {

    try {

        const {
            userId,
            phoneNumber
        } = req.body;


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


        const number =
            String(phoneNumber).replace(/\D/g, "");


        if (
            number.length < 10 ||
            number.length > 15
        ) {
            return res.status(400).json({
                success: false,
                message: "Invalid WhatsApp number"
            });
        }


        // Generate UNIQUE session ID
        const sessionId =
            generateSessionId();


        console.log(
            `Creating WhatsApp session: ${sessionId}`
        );

        console.log(
            `User: ${userId}`
        );

        console.log(
            `Phone: ${number}`
        );


        // Start WhatsApp session
        const session =
            await startSession(
                sessionId,
                number
            );


        let qr =
            getQR(sessionId);


        if (!qr) {

            qr =
                await waitForQR(
                    sessionId,
                    20000
                );
        }


        return res.json({

            success: true,

            userId: userId,

            sessionId: sessionId,

            phoneNumber: number,

            connected:
                session.connected || false,

            qr: qr || null,

            message: qr
                ? "Scan QR using WhatsApp"
                : "QR is being generated"

        });


    } catch (error) {

        console.error(
            "Start Session Error:",
            error
        );


        return res.status(500).json({

            success: false,

            message: error.message

        });

    }

});


router.get("/:sessionId", (req, res) => {

    const sessionId =
        String(req.params.sessionId);


    const session =
        getSession(sessionId);


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

            sessionId: sessionId,

            phoneNumber:
                session.phoneNumber,

            connectedNumber:
                session.connectedNumber,

            qr: null

        });

    }


    return res.json({

        success: true,

        connected: false,

        sessionId: sessionId,

        phoneNumber:
            session.phoneNumber,

        qr:
            getQR(sessionId)

    });

});


module.exports = router;