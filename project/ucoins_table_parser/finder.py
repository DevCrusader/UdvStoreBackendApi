from typing import Tuple, List

import pandas as pd


def binary_search(array, item, left, right):
    if right - left == 1:
        return right

    middle = left + (right - left) // 2

    if array[middle] >= item:
        return binary_search(array, item, left, middle)
    return binary_search(array, item, middle, right)


class Finder:
    def __init__(self, file_path: str):
        full_name_list = [row.values[0] for index, row in pd.read_excel(file_path).iterrows()]

        self.full_name_list = full_name_list
        self.last_name_list = [item.strip().split(" ")[0] for item in self.full_name_list]
        self.list_length = len(full_name_list)

    def find_name(self, name: str) -> tuple[bool, str | None]:
        split_name = name.strip().split(" ")

        if len(split_name) == 3:
            return False, " ".join(split_name)

        if len(split_name) == 1:
            raise ValueError("Name must contain lastname and firstname.")

        find_ln, find_fn = split_name

        searched_last_name_index = binary_search(self.last_name_list, find_ln, 0, len(self.last_name_list))
        result = None

        while result is None:
            try:
                if searched_last_name_index == self.list_length:
                    break

                searched_ln, searched_fn, _ = self.full_name_list[searched_last_name_index].strip().split(" ", 2)

                if searched_ln == find_ln and searched_fn == find_fn:
                    result = self.full_name_list[searched_last_name_index]
                else:
                    searched_last_name_index += 1
            except ValueError:
                break

        if result is None:
            return True, None

        return False, result

