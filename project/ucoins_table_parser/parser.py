import pandas as pd
import os.path

from json import dumps

from user_class import User
from finder import Finder


def ucoins_table_parser(file_path: str, additional_file_path: str) -> (list, list):
    df = pd.read_excel(file_path, usecols=["ФИО", "Активность", "Ucoins", "Сувенирка", "Сумма"])

    finder = Finder(additional_file_path)

    users_list = []
    user_errors = []
    cur_user = None

    for index, row in df.iterrows():
        name, replenishment_reason, replenishment_count, write_off_reason, write_off_count = row.values

        if type(name) is str:
            error, full_name = finder.find_name(name)

            if not error:
                user = User(full_name)

                users_list.append(user)
                cur_user = user
            else:
                user_errors.append((name, "У данного пользователя не удалось найти полное ФИО."))
                cur_user = None
            continue

        if cur_user is not None:
            if type(replenishment_reason) is str:
                try:
                    cur_user.add_replenishment(replenishment_reason, int(replenishment_count))
                except ValueError:
                    print(f"Can not add replenishment for {cur_user.full_name}, "
                          f"some error with {replenishment_reason} count.")

            if type(write_off_reason) is str:
                if write_off_reason != "Итог за сувенирку":
                    try:
                        cur_user.add_write_off(write_off_reason, int(write_off_count))
                    except ValueError:
                        print(f"Can not add write-off for {cur_user.full_name}, "
                              f"some error with {write_off_reason} count.")

    jsonable = []
    for item in users_list:
        try:
            jsonable.append(item.return_as_object())
        except ValueError:
            user_errors.append((item.get_full_name(),
                                "У данного пользователя некотороая ошибка с причинами пополнений/списаний."))

    return jsonable, user_errors


if __name__ == '__main__':
    # UCOINS_TABLE = "UCoins.xlsx"

    while UCOINS_TABLE := input("Enter the ucoins tables path: "):
        if UCOINS_TABLE.split(".")[-1] != "xlsx":
            print("The ucoins tables must have the XLSX extension.")
            continue
        if not os.path.isfile(UCOINS_TABLE):
            print("Could not find this file.")
            continue
        print("Successfully!!", end="\n\n")
        break

    while ADDITIONAL_FULL_NAME_TABLE := input("Enter the additional tables with user's full names path: "):
        if ADDITIONAL_FULL_NAME_TABLE.split(".")[-1] != "xlsx":
            print("The ucoins tables must have the XLSX extension.")
            continue
        if not os.path.isfile(ADDITIONAL_FULL_NAME_TABLE):
            print("Could not find this file.")
            continue
        print("Successfully!!", end="\n\n")
        break

    result, errors = ucoins_table_parser(UCOINS_TABLE, ADDITIONAL_FULL_NAME_TABLE)

    OUTPUT_FOLDER_PATH = input("Enter core path to the folder where the output files will be saved."
                               "Leave it empty to save in current folder.")

    if OUTPUT_FOLDER_PATH and OUTPUT_FOLDER_PATH[-1] != "/":
        OUTPUT_FOLDER_PATH += "/"

    with open(f"{OUTPUT_FOLDER_PATH}result.json", mode="w+", encoding="utf-8") as of:
        of.write(dumps(result, indent=4, ensure_ascii=False))

    with open(f"{OUTPUT_FOLDER_PATH}ErrorList.json", mode="w+", encoding="utf-8") as of:
        of.write(dumps(errors, indent=4, ensure_ascii=False))

    print(f"The result was written to {OUTPUT_FOLDER_PATH}result.json, "
          f"{len(result)} users were successfully converted.")
    print(f"{len(errors)} user with error was written to {OUTPUT_FOLDER_PATH}ErrorList.json")
