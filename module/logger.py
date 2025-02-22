import logging

class Logger:
    def __init__(self, name=__name__, log_file="app.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Create a console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Create a file handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        # Create a formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Set formatter for handlers
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        # Add handlers to the logger
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def log(self, level, message):
        if level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        else:
            self.logger.debug(message)
