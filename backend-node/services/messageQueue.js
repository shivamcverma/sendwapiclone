const queues = new Map();

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getQueue(sessionId) {

    if (!queues.has(sessionId)) {

        queues.set(sessionId, {
            running: false,
            jobs: []
        });

    }

    return queues.get(sessionId);
}


async function processQueue(sessionId) {

    const queue = getQueue(sessionId);

    if (queue.running) {
        return;
    }

    queue.running = true;

    try {

        while (queue.jobs.length > 0) {

            const job = queue.jobs.shift();

            try {

                const result = await job.send();

                job.resolve(result);

            } catch (error) {

                job.reject(error);

            }

            /*
             * Wait before next WhatsApp message
             *
             * 3-5 seconds random delay
             */

            if (queue.jobs.length > 0) {

                const delay =
                    Math.floor(
                        Math.random() * 2000
                    ) + 3000;

                console.log(
                    `Waiting ${delay}ms before next message...`
                );

                await sleep(delay);
            }

        }

    } finally {

        queue.running = false;

        /*
         * Queue empty hone par cleanup
         */

        if (queue.jobs.length === 0) {
            queues.delete(sessionId);
        }

    }
}


function addToQueue(sessionId, sendFunction) {

    return new Promise((resolve, reject) => {

        const queue = getQueue(sessionId);

        queue.jobs.push({

            send: sendFunction,

            resolve,

            reject

        });

        processQueue(sessionId);

    });

}


function getQueueStatus(sessionId) {

    const queue = queues.get(sessionId);

    if (!queue) {

        return {
            running: false,
            pending: 0
        };

    }

    return {

        running: queue.running,

        pending: queue.jobs.length

    };

}


module.exports = {
    addToQueue,
    getQueueStatus
};