const generateApiKey = require("../utils/generateApiKey");

const apiKeys = {};

function createApiKey(userId) {

    const apiKey = generateApiKey();

    apiKeys[apiKey] = userId;

    return apiKey;
}

function getUserByApiKey(apiKey) {
    return apiKeys[apiKey];
}

module.exports = {
    createApiKey,
    getUserByApiKey
};