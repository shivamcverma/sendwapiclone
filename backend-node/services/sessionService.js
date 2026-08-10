const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestWaWebVersion
} = require("@whiskeysockets/baileys");

const QRCode = require("qrcode");
const fs = require("fs");
const path = require("path");

const sessions = {};

function cleanNumber(number) {
    return String(number || "").replace(/\D/g, "");
}

function getConnectedNumber(sock) {
    if (!sock?.user?.id) {
        return null;
    }

    return cleanNumber(
        sock.user.id
            .split(":")[0]
            .split("@")[0]
    );
}

async function startSession(userId, phoneNumber) {
    if (!phoneNumber) {
        throw new Error("WhatsApp number is required");
    }

    if (sessions[String(userId)]) {
        console.log(
            `Existing session for user ${userId} found. Reusing it.`
        );

        return sessions[String(userId)];
    }

    const sessionPath = path.join(
        __dirname,
        "..",
        "sessions",
        userId
    );

    fs.mkdirSync(sessionPath, {
        recursive: true
    });

    const { state, saveCreds } =
        await useMultiFileAuthState(sessionPath);
    const {
        version,
        isLatest
    } = await fetchLatestWaWebVersion();

    console.log(
        `WhatsApp Web Version: ${version.join(".")}`
    );

    console.log(
        `Is Latest: ${isLatest}`
    );

    const sock = makeWASocket({
        version,
        auth: state,
        browser: [
            "Ubuntu",
            "Chrome",
            "20.0.04"
        ]
    });

    sessions[userId] = {
        sock,
        userId,
        phoneNumber,
        qr: null,
        qrImage: null,
        connected: false,
        connectedNumber: null
    };

    sock.ev.on("creds.update", saveCreds);

    sock.ev.on(
        "connection.update",
        async ({ qr, connection, lastDisconnect }) => {

            if (qr) {
                try {
                    sessions[userId].qr = qr;

                    sessions[userId].qrImage =
                        await QRCode.toDataURL(qr);

                } catch (error) {
                    console.error(
                        "QR Error:",
                        error.message
                    );
                }
            }

            if (connection === "open") {

                const connectedNumber =
                    getConnectedNumber(sock);

                console.log(
                    `WhatsApp connected: ${connectedNumber}`
                );

                if (
                    connectedNumber !== phoneNumber
                ) {

                    console.log(
                        `Wrong number. Expected ${phoneNumber}, got ${connectedNumber}`
                    );

                    try {
                        await sock.logout();
                    } catch (error) {
                        console.error(
                            "Logout Error:",
                            error.message
                        );
                    }

                    delete sessions[userId];

                    return;
                }

                sessions[userId].connected = true;
                sessions[userId].connectedNumber =
                    connectedNumber;

                sessions[userId].qr = null;
                sessions[userId].qrImage = null;

                console.log(
                    `Connected successfully: ${phoneNumber}`
                );
            }

            if (connection === "close") {

                const reason =
                    lastDisconnect?.error?.output?.statusCode;

                delete sessions[userId];

                if (
                    reason !== DisconnectReason.loggedOut
                ) {
                    setTimeout(() => {
                        startSession(
                            userId,
                            phoneNumber
                        );
                    }, 3000);
                }
            }
        }
    );

    return sessions[userId];
}

function getSessionById(sessionId) {
    return sessions[String(sessionId)] || null;
}

function getSession(userId) {
    return sessions[String(userId)] || null;
}

function getQR(userId) {
    return sessions[String(userId)]?.qrImage || null;
}

function waitForQR(userId, timeout = 15000) {
    return new Promise((resolve) => {

        const start = Date.now();

        const check = () => {

            const session =
                sessions[String(userId)];

            if (!session) {
                return resolve(null);
            }

            if (session.qrImage) {
                return resolve(session.qrImage);
            }

            if (session.connected) {
                return resolve(null);
            }

            if (Date.now() - start >= timeout) {
                return resolve(null);
            }

            setTimeout(check, 300);
        };

        check();
    });
}

function deleteSession(userId) {
    delete sessions[String(userId)];
}

function getAllSessions() {
    return sessions;
}


module.exports = {
    startSession,
    getSession,
    getSessionById,
    getQR,
    waitForQR,
    deleteSession,
    getAllSessions
};