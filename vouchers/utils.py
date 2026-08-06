import random
import string

CHARACTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_voucher():

    return "".join(
        random.choices(
            CHARACTERS,
            k=6,
        )
    )