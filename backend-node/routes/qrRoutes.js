const express = require("express");

const router = express.Router();

const {
    startSession,
    waitForQR,
    getSession,
    getSessionById,
    getAllSessions,
    getQRBySessionId
} = require("../services/sessionService");


router.post("/start", async (req, res) => {

    try {

        console.log(
            "========== QR START =========="
        );

        console.log(
            "QR START BODY:",
            req.body
        );


        const {
            userId,
            phoneNumber
        } = req.body;


        if (!userId) {

            return res.status(400).json({

                success: false,

                message:
                    "userId is required"

            });

        }


        if (!phoneNumber) {

            return res.status(400).json({

                success: false,

                message:
                    "phoneNumber is required"

            });

        }


        const number =
            String(phoneNumber)
                .replace(/\D/g, "");


        console.log(
            "USER ID:",
            userId
        );

        console.log(
            "PHONE:",
            number
        );


        // ==========================================
        // START / GET EXISTING SESSION
        // ==========================================

        const session =
            await startSession(
                userId,
                number
            );


        if (!session) {

            return res.status(500).json({

                success: false,

                message:
                    "Session could not be created"

            });

        }


        console.log(
            "SESSION CREATED:",
            session.sessionId
        );


        console.log(
            "ACTIVE SESSIONS:",
            Object.keys(
                getAllSessions()
            )
        );


        // ==========================================
        // GET QR
        // ==========================================

        let qr =
            session.qrImage || null;


        if (!qr && !session.connected) {

            qr = await waitForQR(
                session.sessionId,
                20000
            );

        }


        // ==========================================
        // GET CURRENT SESSION
        // ==========================================

        const currentSession =
            getSessionById(
                session.sessionId
            );


        console.log(
            "CURRENT SESSION:",
            currentSession?.sessionId
        );


        console.log(
            "CURRENT SESSIONS:",
            Object.keys(
                getAllSessions()
            )
        );


        if (!currentSession) {

            return res.status(500).json({

                success: false,

                message:
                    "Session could not be created"

            });

        }


        // ==========================================
        // RESPONSE
        // ==========================================

        return res.json({

            success: true,

            userId:
                String(userId),

            sessionId:
                currentSession.sessionId,

            phoneNumber:
                currentSession.phoneNumber,

            connected:
                currentSession.connected,

            connectedNumber:
                currentSession.connectedNumber,

            qr:
                qr ||
                currentSession.qrImage ||
                null

        });


    } catch (error) {

        console.error(
            "QR START ERROR:",
            error
        );


        return res.status(500).json({

            success: false,

            message:
                error.message

        });

    }

});




/* =====================================================
   QR STATUS
   GET /api/qr/:sessionId
===================================================== */

router.get(
    "/:sessionId",
    (req, res) => {

        try {

            const sessionId =
                String(
                    req.params.sessionId
                );


            console.log(
                "QR STATUS SESSION:",
                sessionId
            );


            const session =
                getSessionById(
                    sessionId
                );


            console.log(
                "GET SESSION BY ID:",
                sessionId
            );


            console.log(
                "SESSION FOUND:",
                !!session
            );


            /* =========================================
               SESSION NOT FOUND
            ========================================= */

            if (!session) {

                return res.status(404).json({

                    success: false,

                    connected: false,

                    qr: null,

                    message:
                        "Session not found"

                });

            }


            /* =========================================
               CONNECTED
            ========================================= */

            if (
                session.connected
            ) {

                return res.json({

                    success: true,

                    connected: true,

                    sessionId:
                        session.sessionId,

                    phoneNumber:
                        session.phoneNumber,

                    connectedNumber:
                        session.connectedNumber,

                    qr: null

                });

            }


            /* =========================================
               WAITING FOR QR
            ========================================= */

            return res.json({

                success: true,

                connected: false,

                sessionId:
                    session.sessionId,

                phoneNumber:
                    session.phoneNumber,

                qr:
                    getQRBySessionId(
                        sessionId
                    )

            });


        } catch (error) {

            console.error(
                "QR STATUS ERROR:",
                error
            );


            return res.status(500).json({

                success: false,

                message:
                    error.message

            });

        }

    }
);


module.exports = router;