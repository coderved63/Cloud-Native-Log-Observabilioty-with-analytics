const winston = require('winston');
const { sendLog } = require('./kafka');

const logger = winston.createLogger({
  level: 'debug',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [new winston.transports.Console()],
});

function debug(message) {
  logger.debug(message);
  sendLog('DEBUG', message);
}

function info(message) {
  logger.info(message);
  sendLog('INFO', message);
}

function warn(message) {
  logger.warn(message);
  sendLog('WARNING', message);
}

function error(message) {
  logger.error(message);
  sendLog('ERROR', message);
}

function critical(message) {
  logger.error(`[CRITICAL] ${message}`);
  sendLog('CRITICAL', message);
}

module.exports = { debug, info, warn, error, critical };
