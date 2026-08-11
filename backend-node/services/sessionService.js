
const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestWaWebVersion
} = require("@whiskeysockets/baileys");

const QRCode = require("qrcode");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const sessions = {};

const SESSIONS_DIR = path.join(__dirname, "..", "sessions");

function cleanNumber(number) {
    return String(number || "").replace(/\D/g, "");
}

function generateSessionId() {
    return "wa_" + crypto.randomBytes(16).toString("hex");
}

function getConnectedNumber(sock) {
    if (!sock?.user?.id) {
        console.log("CONNECTED NUMBER: sock.user.id NOT FOUND");
        return null;
    }

    const number = cleanNumber(
        sock.user.id.split(":")[0].split("@")[0]
    );

    console.log("CONNECTED NUMBER FROM WHATSAPP:", number);

    return number;
}

async function startSession(
    userId,
    phoneNumber,
    existingSessionId = null
) {
    console.log("\n========== START SESSION ==========");
    console.log("USER ID:", userId);
    console.log("PHONE:", phoneNumber);
    console.log("EXISTING SESSION ID:", existingSessionId);
    console.log("PROCESS:", process.pid);

    if (!phoneNumber) {
        throw new Error("WhatsApp number is required");
    }

    const cleanPhoneNumberValue =
        cleanNumber(phoneNumber);

    /*
     * Existing session check
     */
    const existingUserSession =
        Object.values(sessions).find(
            session =>
                String(session.userId) === String(userId) &&
                session.phoneNumber === cleanPhoneNumberValue
        );

    if (existingUserSession) {

        console.log(
            "EXISTING SESSION FOUND:",
            existingUserSession.sessionId
        );

        return existingUserSession;
    }

    /*
     * IMPORTANT:
     * sessionId ko USE karne se pehle declare karo
     */
    const sessionId =
        existingSessionId ||
        "wa_" +
        crypto.randomBytes(8).toString("hex");

    console.log(
        "CREATED SESSION ID:",
        sessionId
    );

    /*
     * Ab session object banao
     */
    const session = {
        sessionId,
        userId: String(userId),
        phoneNumber: cleanPhoneNumberValue,
        sock: null,
        qr: null,
        qrImage: null,
        connected: false,
        connectedNumber: null
    };

    /*
     * IMPORTANT:
     * sessions mein immediately store karo
     */
    sessions[sessionId] = session;

    console.log(
        "SESSION STORED:",
        sessionId
    );

    console.log(
        "CURRENT SESSIONS:",
        Object.keys(sessions)
    );

    // YAHAN aapka Baileys / WhatsApp socket creation code rahega
    // const sock = makeWASocket(...)

    return session;
}

async function restoreSession(userId, phoneNumber, sessionId) {
    console.log("\n========== RESTORE SESSION ==========");
    console.log("USER ID:", userId);
    console.log("PHONE:", phoneNumber);
    console.log("SESSION ID:", sessionId);

    try {
        const session = await startSession(
            userId,
            phoneNumber,
            sessionId
        );

        console.log(
            "RESTORE STARTSESSION RESULT:",
            session ? session.sessionId : null
        );

        console.log(
            "SESSIONS AFTER RESTORE:",
            Object.keys(sessions)
        );

        if (session) {
            console.log(
                "SESSION RESTORED SUCCESSFULLY:",
                session.sessionId
            );
        } else {
            console.log(
                "RESTORE RETURNED NULL:",
                sessionId
            );
        }

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

        console.error(
            "RESTORE ERROR STACK:",
            error.stack
        );

        return null;
    }
}

async function restoreAllSessions() {
    console.log("\n========================================");
    console.log("RESTORING SAVED WHATSAPP SESSIONS");
    console.log("========================================");

    console.log("SESSIONS DIR:", SESSIONS_DIR);
    console.log("SESSIONS DIR EXISTS:", fs.existsSync(SESSIONS_DIR));

    if (!fs.existsSync(SESSIONS_DIR)) {
        console.log("NO SESSIONS DIRECTORY FOUND");
        return;
    }

    const folders = fs.readdirSync(
        SESSIONS_DIR,
        { withFileTypes: true }
    );

    console.log(
        "FOUND SESSION FOLDERS:",
        folders.map(folder => folder.name)
    );

    for (const folder of folders) {
        if (!folder.isDirectory()) {
            console.log(
                "SKIPPING NON-DIRECTORY:",
                folder.name
            );
            continue;
        }

        const userId = folder.name;

        console.log("\n----------------------------------------");
        console.log("RESTORING USER FOLDER:", userId);

        const sessionPath = path.join(
            SESSIONS_DIR,
            userId
        );

        const metadataPath = path.join(
            sessionPath,
            "session.json"
        );

        console.log("SESSION PATH:", sessionPath);
        console.log("METADATA PATH:", metadataPath);
        console.log(
            "METADATA EXISTS:",
            fs.existsSync(metadataPath)
        );
        console.log(
            "CREDS EXISTS:",
            fs.existsSync(
                path.join(sessionPath, "creds.json")
            )
        );

        if (!fs.existsSync(metadataPath)) {
            console.log(
                "SESSION METADATA NOT FOUND:",
                userId
            );
            continue;
        }

        try {
            const metadata = JSON.parse(
                fs.readFileSync(
                    metadataPath,
                    "utf8"
                )
            );

            console.log("READ METADATA:", metadata);

            const savedUserId =
                metadata.userId || userId;

            const savedPhoneNumber =
                metadata.phoneNumber;

            const savedSessionId =
                metadata.sessionId;

            console.log("SAVED USER ID:", savedUserId);
            console.log("SAVED PHONE:", savedPhoneNumber);
            console.log("SAVED SESSION ID:", savedSessionId);

            if (!savedPhoneNumber || !savedSessionId) {
                console.log(
                    "INVALID SESSION METADATA:",
                    userId
                );
                continue;
            }

            console.log(
                "CALLING restoreSession:",
                savedSessionId
            );

            const restored = await restoreSession(
                savedUserId,
                savedPhoneNumber,
                savedSessionId
            );

            console.log(
                "restoreSession RETURNED:",
                restored?.sessionId || null
            );

            console.log(
                "CURRENT ACTIVE SESSIONS:",
                Object.keys(sessions)
            );
        } catch (error) {
            console.error(
                `FAILED TO RESTORE USER ${userId}:`,
                error
            );
        }
    }

    console.log("\n========================================");
    console.log("SESSION RESTORE COMPLETE");
    console.log(
        "ACTIVE SESSIONS:",
        Object.keys(sessions)
    );
    console.log("========================================\n");
}

function getSessionById(sessionId) {
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
        sessions[String(sessionId)] || null;

    console.log(
        "SESSION FOUND:",
        !!session
    );

    return session;
}

function getSession(userId) {
    return Object.values(sessions).find(
        session =>
            String(session.userId) ===
            String(userId)
    ) || null;
}

function getQR(userId) {
    const session = getSession(userId);

    return session?.qrImage || null;
}

function waitForQR(userId, timeout = 15000) {
    return new Promise(resolve => {
        const start = Date.now();

        const check = () => {
            const session = getSession(userId);

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

function deleteSession(sessionId) {
    if (!sessionId) {
        return;
    }

    delete sessions[String(sessionId)];

    console.log(
        "SESSION DELETED MANUALLY:",
        sessionId
    );

    console.log(
        "CURRENT SESSIONS:",
        Object.keys(sessions)
    );
}

function getAllSessions() {
    return sessions;
}

module.exports = {
    startSession,
    restoreSession,
    restoreAllSessions,
    getSession,
    getSessionById,
    getQR,
    waitForQR,
    deleteSession,
    getAllSessions
};
