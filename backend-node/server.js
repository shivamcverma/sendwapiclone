
const express = require("express");
const cors = require("cors");
require("dotenv").config();

const authRoutes = require("./routes/authRoutes");
const messageRoutes = require("./routes/messageRoutes");
const qrRoutes = require("./routes/qrRoutes");

const app = express();

app.use(cors());
app.use(express.json());

app.use("/api/auth", authRoutes);
app.use("/api/whatsapp", messageRoutes);
app.use("/api/qr", qrRoutes);

const PORT = process.env.PORT || 3001;

app.listen(PORT, () => {
    console.log(`WhatsApp Server running on port ${PORT}`);
});
