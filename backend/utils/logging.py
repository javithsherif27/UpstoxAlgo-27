import logging, os, sys

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

class MaskTokenFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            new_args = []
            for a in record.args:
                if isinstance(a, str) and 'Bearer ' in a:
                    new_args.append('Bearer ***masked***')
                else:
                    new_args.append(a)
            record.args = tuple(new_args)
        return True

def configure_logging():
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        stream=sys.stdout
    )
    for h in logging.getLogger().handlers:
        h.addFilter(MaskTokenFilter())


def get_logger(name: str):
    return logging.getLogger(name)
