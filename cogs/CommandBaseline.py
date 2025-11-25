class CommandBaseline():
    def __init__(self, client, cursor, db):
        self.client = client
        self.cursor = cursor
        self.db = db
        print(f"Loaded {self.__class__.__name__} commands")