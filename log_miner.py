"""
Данный файл отвечает за логирование процесса роботы майнера.
Настройки:
log_type - Отвечает за включение и выключение, и тип показываемых логов:
0 - Логи выключены
1 - Все логи включены (логи в консоль + логи flask)
2 - Включены логи flask
3 - Включены собственные логи майнера
"""
import logging

log_type = 3

def create_log_flask():
    if log_type == 0 or log_type == 3:
        log = logging.getLogger('werkzeug')
        log.disabled = True
        return log
    else:
        log = logging.getLogger('werkzeug')
        log.disabled = False
        return log

def create_log_console():
    if log_type == 0 or log_type == 2:
        logger = logging.getLogger('miner')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '', '%')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.disabled = True
        return logger
    else:
        logger = logging.getLogger('miner')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '', '%')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.disabled = False
        return logger