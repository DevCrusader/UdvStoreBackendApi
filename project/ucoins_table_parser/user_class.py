class User:
    def __init__(self, full_name: str):
        self.full_name = full_name.strip()

        # if len(self.full_name.split(" ")) < 3:
        #     raise ValueError("User's full_name must contain three or more parts.")

        self.replenishments = []
        self.write_offs = []

    def __str__(self):
        return f"User: {self.full_name}"

    def get_full_name(self):
        return self.full_name

    def add_replenishment(self, reason: str, count: int | str) -> None:
        if not reason:
            raise ValueError(f"Reason can not be empty.")

        if type(count) is str:
            try:
                count = int(count)
            except ValueError:
                raise ValueError("Count can not be converted to an integer.")

        self.replenishments.append((reason, count))

    def add_write_off(self, reason: str, count: int | str) -> None:
        if not reason:
            raise ValueError("Reason can not be empty.")

        if type(count) is str:
            try:
                count = int(count)
            except ValueError:
                raise ValueError("Count can not be converted to an integer.")

        self.write_offs.append((reason, count))

    def calculate_total_replenishments_count(self) -> int:
        return sum([item[1] for item in self.replenishments])

    def calculate_total_write_offs_count(self) -> int:
        return sum([item[1] for item in self.write_offs])

    def return_as_object(self) -> dict:
        ln, fn, p = self.full_name.split(" ", 2)

        total_balance = self.calculate_total_replenishments_count() - self.calculate_total_write_offs_count()

        if total_balance < 0:
            raise ValueError(f"Total count can not be negative, check {self.full_name} "
                             f"user's replenishments and write-offs lists.")

        return {
            "name": {
                "full_name": self.full_name,
                "last_name": ln,
                "first_name": fn,
                "patronymic": p
            },
            "replenishments": [
                {"reason": reason, "count": count} for reason, count in self.replenishments
            ],
            "write_offs": [
                {"reason": reason, "count": count} for reason, count in self.write_offs
            ],
            "total": total_balance
        }
