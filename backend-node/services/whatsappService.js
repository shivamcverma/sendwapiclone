const {
    getSessionById,
    getAllSessions
} = require("./sessionService");


async function sendMessage(
    sessionId,
    phoneNumber,
    message
) {

    console.log(
        "SEND MESSAGE sessionId:",
        sessionId
    );

    console.log(
        "AVAILABLE SESSIONS:",
        Object.keys(getAllSessions())
    );

    const session =
        getSessionById(sessionId);


    if (!session) {
        throw new Error(
            `WhatsApp session not found for sessionId: ${sessionId}`
        );
    }


    if (!session.connected) {
        throw new Error(
            "WhatsApp session exists but is not connected"
        );
    }


    const sock = session.sock;


    const formattedNumber =
        String(phoneNumber).replace(/\D/g, "");


    const jid =
        `${formattedNumber}@s.whatsapp.net`;


    const result =
        await sock.sendMessage(
            jid,
            {
                text: message
            }
        );


    return {
        messageId:
            result?.key?.id || null,

        phoneNumber:
            formattedNumber
    };
}


module.exports = {
    sendMessage
};