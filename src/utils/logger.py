import logging
import os
import time


__author__ = 'lquiroz'


class Logger(object):
    __instance = None

    def __init__(self):
        pass

    def __new__(cls, name=__name__,
                level=logging.DEBUG,
                output_path=os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                                         'output', 'logs'), **kwargs):

        if not cls.__instance:
            cls.__instance = object.__new__(cls)
            cls.__configure_logger(name=name, level=level, output_path=output_path)

        return cls.__instance

    @classmethod
    def __configure_logger(cls, name, level, output_path):
        # logging.basicConfig(level=level)
        cls.__instance = logging.getLogger(name)
        cls.__instance.setLevel(level)

        # create a file handler
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        fh = logging.FileHandler(os.path.join(output_path, time.strftime('%Y-%m-%d-%H-%M-%S.log')))
        fh.setLevel(level)

        ch = logging.StreamHandler()
        ch.setLevel(level)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # add the handlers to the logger
        cls.__instance.addHandler(fh)
        cls.__instance.addHandler(ch)


if __name__ == '__main__':
    Logger()
