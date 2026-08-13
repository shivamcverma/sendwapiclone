const {
    sendMessage
} = require("../services/whatsappService");


exports.sendMessage =
    async (req, res) => {

        const {
            senderNumber,
            phoneNumber,
            message
        } = req.body;


        /*
         * Validation
         */

        if (
            !senderNumber ||
            !phoneNumber ||
            !message
        ) {

            return res.status(400).json({

                success: false,

                error:
                    "senderNumber, phoneNumber and message are required"

            });

        }


        try {

            console.log(
                "MESSAGE REQUEST:"
            );


            console.log(
                "senderNumber:",
                senderNumber
            );


            console.log(
                "phoneNumber:",
                phoneNumber
            );


            const result =
                await sendMessage(
                    senderNumber,
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
                    new Date()
                        .toISOString()

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