import mariadb

class OperationalError(Exception):
    pass

class SQLError(Exception):
    pass

class UseDB:
    def __init__(self, config:dict) -> None:
        self.configuration = config

    def __enter__(self) -> "cursor":
        try:
            self.conn = mariadb.connect(**self.configuration)
            self.cursor = self.conn.cursor()
            return self.cursor
        except mariadb.OperationalError as err:
            raise OperationalError(err)

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
        if exc_type is mariadb.ProgrammingError:
            raise SQLError(exc_value)
        elif exc_type:
            raise exc_type(exc_value)
