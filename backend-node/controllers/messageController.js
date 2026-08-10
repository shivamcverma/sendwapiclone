const {
    sendMessage
} = require("../services/whatsappService");


exports.sendMessage = async (req, res) => {

    const {
        sessionId,
        phoneNumber,
        message
    } = req.body;


    if (
        !sessionId ||
        !phoneNumber ||
        !message
    ) {

        return res.status(400).json({
            success: false,
            error:
                "sessionId, phoneNumber and message are required"
        });
    }


    try {

        const result =
            await sendMessage(
                sessionId,
                phoneNumber,
                message
            );


        return res.json({

            success: true,

            message:
                "Message sent successfully",

            messageId:
                result.messageId,

            phoneNumber:
                result.phoneNumber,

            timestamp:
                new Date().toISOString()
        });


    } catch (error) {

        console.error(
            "Send Message Error:",
            error
        );


        return res.status(500).json({

            success: false,

            error:
                error.message
        });
    }
};