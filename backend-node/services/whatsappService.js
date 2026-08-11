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
        Object.keys(
            getAllSessions()
        )
    );


    /*
     * Find session using sessionId
     */

    const session =
        getSessionById(
            sessionId
        );


    if (!session) {

        throw new Error(
            `WhatsApp session not found for sessionId: ${sessionId}`
        );

    }


    /*
     * Check connection
     */

    if (!session.connected) {

        throw new Error(
            "WhatsApp session exists but is not connected"
        );

    }


    /*
     * Socket
     */

    const sock =
        session.sock;


    /*
     * Clean phone number
     */

    const formattedNumber =
        String(
            phoneNumber
        ).replace(
            /\D/g,
            ""
        );


    /*
     * WhatsApp JID
     */

    const jid =
        `${formattedNumber}@s.whatsapp.net`;


    /*
     * Send message
     */

    const result =
        await sock.sendMessage(
            jid,
            {
                text: message
            }
        );


    /*
     * Return result
     */

    return {

        messageId:
            result?.key?.id ||
            null,

        phoneNumber:
            formattedNumber

    };

}


module.exports = {
    sendMessage
};