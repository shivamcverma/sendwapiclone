const { startSession, sessions } = require("../services/whatsappService")

exports.generateQR = async (req, res) => {
    const userId = req.params.userId

    if (sessions[userId]) {
        return res.json({ message: "Already connected or session exists" })
    }

    await startSession(userId, res)
}