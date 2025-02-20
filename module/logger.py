import logging

class Logger:
    def __init__(self, name=__name__):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Create a console handler and set level to info
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(ch)

    def log(self, level, message):
        if level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        else:
            self.logger.debug(message)