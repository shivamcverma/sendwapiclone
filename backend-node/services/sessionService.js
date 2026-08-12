
const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason
} = require("@whiskeysockets/baileys");

const QRCode = require("qrcode");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");


/* =====================================================
   SESSIONS
===================================================== */

const sessions = {};


/* =====================================================
   SESSIONS DIRECTORY
===================================================== */

const SESSIONS_DIR =
    path.join(
        __dirname,
        "..",
        "sessions"
    );


/* =====================================================
   HELPERS
===================================================== */

function cleanNumber(number) {

    return String(number || "")
        .replace(/\D/g, "");

}


function generateSessionId() {

    return (
        "wa_" +
        crypto
            .randomBytes(8)
            .toString("hex")
    );

}


function getConnectedNumber(sock) {

    if (!sock?.user?.id) {

        console.log(
            "CONNECTED NUMBER: sock.user.id NOT FOUND"
        );

        return null;

    }


    const number =
        cleanNumber(
            sock.user.id
                .split(":")[0]
                .split("@")[0]
        );


    console.log(
        "CONNECTED NUMBER FROM WHATSAPP:",
        number
    );


    return number;

}


/* =====================================================
   START SESSION
===================================================== */

async function startSession(
    userId,
    phoneNumber,
    existingSessionId = null
) {

    console.log(
        "\n========== START SESSION =========="
    );

    console.log(
        "USER ID:",
        userId
    );

    console.log(
        "PHONE:",
        phoneNumber
    );

    console.log(
        "EXISTING SESSION ID:",
        existingSessionId
    );


    /* =========================================
       VALIDATION
    ========================================= */

    if (!phoneNumber) {
        throw new Error(
            "WhatsApp number is required"
        );
    }


    const cleanPhoneNumberValue =
        cleanNumber(phoneNumber);


    /* =========================================
       CHECK EXISTING USER SESSION
    ========================================= */

    const existingUserSession =
        Object.values(sessions).find(
            session =>
                String(session.userId) ===
                String(userId) &&
                (
                    session.connected === true ||
                    session.connecting === true ||
                    session.qr
                )
        );


    if (existingUserSession) {

        console.log(
            "================================"
        );

        console.log(
            "EXISTING USER SESSION FOUND"
        );

        console.log(
            "SESSION ID:",
            existingUserSession.sessionId
        );

        console.log(
            "CONNECTED:",
            existingUserSession.connected
        );

        console.log(
            "CONNECTING:",
            existingUserSession.connecting
        );

        console.log(
            "QR AVAILABLE:",
            !!existingUserSession.qr
        );

        console.log(
            "================================"
        );


        /*
         * Existing socket/session ko dobara
         * create nahi karna.
         */

        return existingUserSession;
    }


    /* =========================================
       CREATE NEW SESSION
    ========================================= */

    const sessionId =
        existingSessionId ||
        `wa_${crypto.randomBytes(7).toString("hex")}`;


    console.log(
        "CREATING NEW SESSION:",
        sessionId
    );


    /* =================================================
       AUTH DIRECTORY
    ================================================= */

    const authPath =
        path.join(
            SESSIONS_DIR,
            String(userId)
        );


    if (!fs.existsSync(authPath)) {

        fs.mkdirSync(
            authPath,
            {
                recursive: true
            }
        );

    }


    console.log(
        "AUTH PATH:",
        authPath
    );


    /* =================================================
       BAILEYS AUTH
    ================================================= */

    const {
        state,
        saveCreds
    } =
        await useMultiFileAuthState(
            authPath
        );


    /* =================================================
       CREATE SOCKET
    ================================================= */

    console.log(
        "CREATING WHATSAPP SOCKET..."
    );

    console.log(
        "AUTH PATH:",
        authPath
    );

    console.log(
        "AUTH CREDS:",
        state?.creds?.me?.id || "NO AUTHENTICATED USER"
    );
    const sock =
        makeWASocket({

            auth: state,

            printQRInTerminal: false

        });

    sock.ev.on(
       "creds.update",
       saveCreds
    );

    /* =================================================
       SESSION OBJECT
    ================================================= */

    const session = {

        sessionId,

        userId:
            String(userId),

        phoneNumber:
            cleanPhoneNumberValue,

        sock,

        qr: null,

        qrImage: null,

        connected: false,

        connecting: true,

        connectedNumber: null,

        reconnecting: false

    };


    /* =================================================
       STORE SESSION
    ================================================= */

    sessions[sessionId] =
        session;


    console.log(
        "SESSION STORED:",
        sessionId
    );


    console.log(
        "CURRENT SESSIONS:",
        Object.keys(sessions)
    );


    /* =================================================
       SAVE SESSION METADATA
    ================================================= */

    const metadataPath =
        path.join(
            authPath,
            "session.json"
        );


    try {

        fs.writeFileSync(

            metadataPath,

            JSON.stringify(
                {
                    userId:
                        String(userId),

                    phoneNumber:
                        cleanPhoneNumberValue,

                    sessionId:
                        sessionId

                },
                null,
                2
            )

        );


        console.log(
            "SESSION METADATA SAVED"
        );


    } catch (error) {

        console.error(
            "SESSION METADATA SAVE ERROR:",
            error
        );

    }


    /* =================================================
       SAVE BAILEYS CREDENTIALS
    ================================================= */

    sock.ev.on(
        "creds.update",
        saveCreds
    );


    /* =================================================
       CONNECTION UPDATE
    ================================================= */

    sock.ev.on(
        "connection.update",
        async (update) => {

            const {
                connection,
                lastDisconnect,
                qr
            } = update;


            console.log(
                "WHATSAPP CONNECTION UPDATE:",
                connection
            );


            /* =========================================
               QR RECEIVED
            ========================================= */

            if (qr) {

                console.log(
                    "WHATSAPP QR RECEIVED"
                );


                try {

                    session.qr =
                        qr;


                    session.qrImage =
                        await QRCode.toDataURL(
                            qr
                        );


                    console.log(
                        "QR IMAGE GENERATED:",
                        session.sessionId
                    );


                } catch (error) {

                    console.error(
                        "QR GENERATION ERROR:",
                        error
                    );

                }

            }


            /* =========================================
               CONNECTED
            ========================================= */

            if (
                connection ===
                "open"
            ) {

                session.connected =
                    true;

                session.connecting =
                    false;

                session.reconnecting =
                    false;


                session.qr =
                    null;

                session.qrImage =
                    null;


                session.connectedNumber =
                    getConnectedNumber(
                        sock
                    );


                console.log(
                    "================================"
                );

                console.log(
                    "WHATSAPP CONNECTED"
                );

                console.log(
                    "SESSION ID:",
                    session.sessionId
                );

                console.log(
                    "USER ID:",
                    session.userId
                );

                console.log(
                    "PHONE:",
                    session.phoneNumber
                );

                console.log(
                    "CONNECTED NUMBER:",
                    session.connectedNumber
                );

                console.log(
                    "CURRENT SESSIONS:",
                    Object.keys(sessions)
                );

                console.log(
                    "================================"
                );

            }


            /* =========================================
               CONNECTION CLOSED
            ========================================= */

            if (
                connection ===
                "close"
            ) {

                session.connected =
                    false;

                session.connecting =
                    false;


                console.log(
                    "WHATSAPP CONNECTION CLOSED:",
                    session.sessionId
                );


                const statusCode =
                    lastDisconnect
                        ?.error
                        ?.output
                        ?.statusCode;


                console.log(
                    "DISCONNECT STATUS:",
                    statusCode
                );


                /* =====================================
                   LOGGED OUT
                ===================================== */

                if (
                    statusCode ===
                    DisconnectReason.loggedOut
                ) {

                    console.log(
                        "WHATSAPP LOGGED OUT:",
                        session.sessionId
                    );


                    if (
                        sessions[
                            session.sessionId
                        ] === session
                    ) {

                        delete sessions[
                            session.sessionId
                        ];

                    }


                    console.log(
                        "SESSION REMOVED:",
                        session.sessionId
                    );


                    return;

                }


                /* =====================================
                   CONFLICT / REPLACED
                ===================================== */

                if (
                    statusCode === 440
                ) {

                    console.log(
                        "================================"
                    );

                    console.log(
                        "WHATSAPP SESSION CONFLICT"
                    );

                    console.log(
                        "SESSION:",
                        session.sessionId
                    );

                    console.log(
                        "NOT RECONNECTING IMMEDIATELY"
                    );

                    console.log(
                        "================================"
                    );


                    /*
                     * Important:
                     *
                     * 440 conflict par immediately
                     * new socket create nahi karna.
                     *
                     * Warna:
                     *
                     * socket A
                     *    ↓
                     * socket B
                     *    ↓
                     * conflict
                     *    ↓
                     * socket C
                     *    ↓
                     * conflict
                     *
                     * infinite loop banega.
                     */


                    if (
                        sessions[
                            session.sessionId
                        ] === session
                    ) {

                        delete sessions[
                            session.sessionId
                        ];

                    }


                    return;

                }


                /* =====================================
                   OTHER DISCONNECTS
                ===================================== */

                if (
                    session.reconnecting
                ) {

                    console.log(
                        "RECONNECT ALREADY IN PROGRESS:",
                        session.sessionId
                    );

                    return;

                }


                session.reconnecting =
                    true;


                /*
                 * Old session ko remove karo.
                 */

                if (
                    sessions[
                        session.sessionId
                    ] === session
                ) {

                    delete sessions[
                        session.sessionId
                    ];

                }


                console.log(
                    "RECONNECTING AFTER DELAY..."
                );


                /*
                 * Thoda wait karo.
                 */

                setTimeout(
                    async () => {

                        try {

                            /*
                             * Check karo ki kisi
                             * naye session ne same
                             * user ko already claim
                             * to nahi kar liya.
                             */

                            const currentUserSession =
                                Object.values(
                                    sessions
                                ).find(
                                    current =>
                                        String(
                                            current.userId
                                        ) ===
                                        String(userId)
                                );


                            if (
                                currentUserSession
                            ) {

                                console.log(
                                    "USER ALREADY HAS ACTIVE SESSION:",
                                    currentUserSession.sessionId
                                );

                                return;

                            }


                            console.log(
                                "STARTING RECONNECT:",
                                sessionId
                            );


                            await startSession(

                                userId,

                                phoneNumber,

                                sessionId

                            );


                            console.log(
                                "RECONNECT SUCCESS:",
                                sessionId
                            );


                        } catch (error) {

                            console.error(
                                "RECONNECT ERROR:",
                                error
                            );

                        }

                    },

                    5000
                );

            }

        }
    );


    /* =================================================
       RETURN SESSION
    ================================================= */

    return session;

}


/* =====================================================
   RESTORE SINGLE SESSION
===================================================== */

async function restoreSession(
    userId,
    phoneNumber,
    sessionId
) {

    console.log(
        "\n========== RESTORE SESSION =========="
    );

    console.log(
        "USER ID:",
        userId
    );

    console.log(
        "PHONE:",
        phoneNumber
    );

    console.log(
        "SESSION ID:",
        sessionId
    );


    try {

        const session =
            await startSession(
                userId,
                phoneNumber,
                sessionId
            );


        console.log(
            "RESTORE RESULT:",
            session?.sessionId || null
        );


        console.log(
            "ACTIVE SESSIONS:",
            Object.keys(sessions)
        );


        return session;


    } catch (error) {

        console.error(
            "SESSION RESTORE ERROR:",
            error
        );


        console.error(
            "RESTORE ERROR MESSAGE:",
            error.message
        );


        return null;

    }

}


/* =====================================================
   RESTORE ALL SESSIONS
===================================================== */

async function restoreAllSessions() {

    console.log(
        "\n========================================"
    );

    console.log(
        "RESTORING SAVED WHATSAPP SESSIONS"
    );

    console.log(
        "========================================"
    );


    console.log(
        "SESSIONS DIR:",
        SESSIONS_DIR
    );


    console.log(
        "SESSIONS DIR EXISTS:",
        fs.existsSync(
            SESSIONS_DIR
        )
    );


    if (
        !fs.existsSync(
            SESSIONS_DIR
        )
    ) {

        console.log(
            "NO SESSIONS DIRECTORY FOUND"
        );

        return;

    }


    const folders =
        fs.readdirSync(
            SESSIONS_DIR,
            {
                withFileTypes:
                    true
            }
        );


    console.log(
        "FOUND SESSION FOLDERS:",
        folders.map(
            folder =>
                folder.name
        )
    );


    for (
        const folder of folders
    ) {

        if (
            !folder.isDirectory()
        ) {

            continue;

        }


        const userId =
            folder.name;


        const sessionPath =
            path.join(
                SESSIONS_DIR,
                userId
            );


        const metadataPath =
            path.join(
                sessionPath,
                "session.json"
            );


        console.log(
            "\nRESTORING USER:",
            userId
        );


        console.log(
            "SESSION PATH:",
            sessionPath
        );


        console.log(
            "METADATA PATH:",
            metadataPath
        );


        if (
            !fs.existsSync(
                metadataPath
            )
        ) {

            console.log(
                "SESSION METADATA NOT FOUND:",
                userId
            );


            continue;

        }


        try {

            const metadata =
                JSON.parse(
                    fs.readFileSync(
                        metadataPath,
                        "utf8"
                    )
                );


            console.log(
                "READ METADATA:",
                metadata
            );


            const savedUserId =
                metadata.userId ||
                userId;


            const savedPhoneNumber =
                metadata.phoneNumber;


            const savedSessionId =
                metadata.sessionId;


            console.log(
                "SAVED USER ID:",
                savedUserId
            );


            console.log(
                "SAVED PHONE:",
                savedPhoneNumber
            );


            console.log(
                "SAVED SESSION ID:",
                savedSessionId
            );


            if (
                !savedPhoneNumber ||
                !savedSessionId
            ) {

                console.log(
                    "INVALID SESSION METADATA:",
                    userId
                );


                continue;

            }


            await restoreSession(

                savedUserId,

                savedPhoneNumber,

                savedSessionId

            );


        } catch (error) {

            console.error(
                `FAILED TO RESTORE USER ${userId}:`,
                error
            );

        }

    }


    console.log(
        "\n========================================"
    );

    console.log(
        "SESSION RESTORE COMPLETE"
    );

    console.log(
        "ACTIVE SESSIONS:",
        Object.keys(sessions)
    );

    console.log(
        "========================================\n"
    );

}


/* =====================================================
   GET SESSION BY USER ID
===================================================== */

function getSession(userId) {

    return (
        Object.values(
            sessions
        ).find(
            session =>
                String(
                    session.userId
                ) ===
                String(userId)
        ) || null
    );

}


/* =====================================================
   GET SESSION BY SESSION ID
===================================================== */

function getSessionById(
    sessionId
) {

    console.log(
        "GET SESSION BY ID:",
        sessionId
    );


    console.log(
        "AVAILABLE SESSION IDS:",
        Object.keys(sessions)
    );


    if (!sessionId) {

        return null;

    }


    const session =
        sessions[
            String(sessionId)
        ] || null;


    console.log(
        "SESSION FOUND:",
        !!session
    );


    return session;

}


/* =====================================================
   GET QR BY USER ID
===================================================== */

function getQR(userId) {

    const session =
        getSession(userId);


    return (
        session?.qrImage ||
        null
    );

}


/* =====================================================
   GET QR BY SESSION ID
===================================================== */

function getQRBySessionId(
    sessionId
) {

    const session =
        getSessionById(
            sessionId
        );


    if (!session) {

        return null;

    }


    return (
        session.qrImage ||
        null
    );

}


/* =====================================================
   WAIT FOR QR
===================================================== */

function waitForQR(
    sessionId,
    timeout = 20000
) {

    return new Promise(
        resolve => {

            const start =
                Date.now();


            const check = () => {

                const session =
                    getSessionById(
                        sessionId
                    );


                /* =====================================
                   SESSION NOT FOUND
                ===================================== */

                if (!session) {

                    console.log(
                        "WAIT QR: SESSION NOT FOUND:",
                        sessionId
                    );


                    return resolve(
                        null
                    );

                }


                /* =====================================
                   QR AVAILABLE
                ===================================== */

                if (
                    session.qrImage
                ) {

                    console.log(
                        "WAIT QR: QR FOUND:",
                        sessionId
                    );


                    return resolve(
                        session.qrImage
                    );

                }


                /* =====================================
                   CONNECTED WITHOUT QR
                ===================================== */

                if (
                    session.connected
                ) {

                    console.log(
                        "WAIT QR: SESSION CONNECTED:",
                        sessionId
                    );


                    return resolve(
                        null
                    );

                }


                /* =====================================
                   TIMEOUT
                ===================================== */

                if (
                    Date.now() -
                    start >=
                    timeout
                ) {

                    console.log(
                        "QR WAIT TIMEOUT:",
                        sessionId
                    );


                    return resolve(
                        null
                    );

                }


                setTimeout(
                    check,
                    300
                );

            };


            check();

        }
    );

}


/* =====================================================
   DELETE SESSION
===================================================== */

function deleteSession(
    sessionId
) {

    if (!sessionId) {

        return;

    }


    const id =
        String(
            sessionId
        );


    if (
        sessions[id]
    ) {

        delete sessions[id];

    }


    console.log(
        "SESSION DELETED:",
        id
    );


    console.log(
        "CURRENT SESSIONS:",
        Object.keys(sessions)
    );

}


/* =====================================================
   GET ALL SESSIONS
===================================================== */

function getAllSessions() {

    return sessions;

}


/* =====================================================
   EXPORT
===================================================== */

module.exports = {

    startSession,

    restoreSession,

    restoreAllSessions,

    getSession,

    getSessionById,

    getQR,

    getQRBySessionId,

    waitForQR,

    deleteSession,

    getAllSessions

};
