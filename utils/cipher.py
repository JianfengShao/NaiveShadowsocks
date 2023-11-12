import random
import json


class Cipher:
    def __init__(self, encode_password: bytearray, decode_password: bytearray):
        self.encode_password = encode_password.copy()
        self.decode_password = decode_password.copy()

    def encode(self, bs: bytearray):
        for i, v in enumerate(bs):
            bs[i] = self.encode_password[v]

    def decode(self, bs: bytearray):
        for i, v in enumerate(bs):
            bs[i] = self.decode_password[v]

    @classmethod
    def newCipher(cls, password):
        encode_password = bytearray(password)
        decode_password = encode_password.copy()
        for i, v in enumerate(encode_password):
            decode_password[v] = i

        return Cipher(encode_password, decode_password)


def generate_password():
    identity_password = list(range(256))
    password = identity_password.copy()
    random.shuffle(password)

    # 保存到文件
    with open('password.json', 'w') as file:
        json.dump(password, file)


def load_password():
    try:
        with open('password.json', 'r') as file:
            password = json.load(file)
    except FileNotFoundError:
        generate_password()
        print("- Password not found !!! \n- Generated a new one.")
        password = load_password()

    return password
