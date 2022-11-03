from json import load
from .serializers import UserPureSerializer, CustomerPureSerializer, \
    BalanceReplenishPureSerializer, BalanceWriteOffPureSerializer
import os.path


class UserRegisterByJSONFile:
    def __init__(self, json_file_path: str):
        self.file_path = json_file_path

        if json_file_path.split(".")[-1] != "json":
            raise ValueError("Current file is not json.")

        if not os.path.isfile(json_file_path):
            raise ValueError("This file does not exist.")

        with open(json_file_path) as json_file:
            self.user_list = load(json_file)

        self.error_user_list = []
        self.success_user_list = []
        self.last_registered_user_index = -1

    def show_full_user_list(self) -> list[dict]:
        return self.user_list

    def register_next_user(self) -> (bool, str):
        if self.last_registered_user_index == len(self.user_list):
            raise IndexError("All users has been registered, check error_user_list if somebody is missing.")
        self.last_registered_user_index += 1
        try:
            user_id, customer_id = register(self.user_list[self.last_registered_user_index])
        except ValueError as err:
            return False, err
        else:
            return True, f"User_id is #{user_id} and customer_id is #{customer_id}"

    def register_one_user(self) -> None:
        try:
            registered, comment = self.register_next_user()

            if registered:
                self.success_user_list.append(self.user_list[self.last_registered_user_index])
                print(f"{comment} has been successfully registered.")
            else:
                self.error_user_list.append((self.user_list[self.last_registered_user_index], comment))
                print(f"Не удалось зарегистрировать данного пользователя по причине: {comment}")

        except IndexError as err:
            print(err)

    def register_all_user(self) -> None:
        for _ in range(self.unregistered_users_count()):
            self.register_one_user()
        print("All users has been registered, check error_user_list if somebody is missing.")

    def unregistered_users_count(self):
        return len(self.user_list) - (self.last_registered_user_index + 1)


def register(user_obj: dict) -> (int, int):
    user_name = user_obj.get("name")

    if user_name is None:
        raise ValueError("User object does not contain name field.")

    user_ln = user_name.get("last_name")
    user_fn = user_name.get("first_name")
    user_p = user_name.get("patronymic")

    if user_ln is None or user_fn is None or user_p is None:
        raise ValueError("User name fields does not contain one of this field: last_name, first_name, patronymic.")

    username = "_".join([user_ln, user_fn, user_p])

    user_serializer = UserPureSerializer(data={
        "username": username,
        "password": username
    })

    if user_serializer.is_valid():
        user = user_serializer.save()

        customer_serializer = CustomerPureSerializer(data={
            "user": user.id,
            "last_name": user_ln,
            "first_name": user_fn,
            "patronymic": user_p,
        })

        if customer_serializer.is_valid():
            customer = customer_serializer.save()

            replenishments = user_obj.get("replenishments", [])

            for replenishment in replenishments:
                br = BalanceReplenishPureSerializer(data={
                    "user": user.id,
                    "admin_id": user.id,
                    "comment": replenishment.get("reason", ""),
                    "count": int(replenishment.get("count", 0))
                })

                if br.is_valid():
                    br.save()

            write_offs = user_obj.get("write_offs", [])

            for write_off in write_offs:
                bwo = BalanceWriteOffPureSerializer(data={
                    "user": user.id,
                    "admin_id": user.id,
                    "comment": write_off.get("reason", ""),
                    "count": int(write_off.get("count", 0))
                })

                if bwo.is_valid():
                    bwo.save()

            return user.id, customer.id

        raise ValueError(str(customer_serializer.errors))

    raise ValueError(str(user_serializer.errors))
