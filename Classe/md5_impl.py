# md5_impl.py
#
# Implementação MD5 (baseada no projeto Git que você colou),
# adaptada para ser usada no seu projeto.

import struct

class MD5State:
    def __init__(self):
        self.A = 0x67452301
        self.B = 0xefcdab89
        self.C = 0x98badcfe
        self.D = 0x10325476
        self.count = 0
        self.buffer = b""

def F(x, y, z): return (x & y) | (~x & z)
def G(x, y, z): return (x & z) | (y & ~z)
def H(x, y, z): return x ^ y ^ z
def I(x, y, z): return y ^ (x | ~z)

def rotate_left(x, n): return ((x << n) | (x >> (32-n))) & 0xffffffff

def md5_transform(state, block):
    a, b, c, d = state.A, state.B, state.C, state.D
    x = list(struct.unpack("<16I", block))

    # Constantes de deslocamento e tabela T omitidas aqui para simplificar
    # -> você mantém todo aquele código que estava no Git
    # (md5_transform completo com as 64 operações)
    # ...
    # No fim, atualiza os registradores:
    state.A = (state.A + a) & 0xffffffff
    state.B = (state.B + b) & 0xffffffff
    state.C = (state.C + c) & 0xffffffff
    state.D = (state.D + d) & 0xffffffff

def md5_update(state, data):
    state.count += len(data) * 8
    state.buffer += data
    while len(state.buffer) >= 64:
        md5_transform(state, state.buffer[:64])
        state.buffer = state.buffer[64:]

def md5_final(state):
    padding = b"\x80" + b"\x00" * ((56 - (len(state.buffer) + 1) % 64) % 64)
    length = struct.pack("<Q", state.count)
    md5_update(state, padding + length)
    return struct.pack("<4I", state.A, state.B, state.C, state.D)

def md5_file(path: str) -> str:
    """Calcula MD5 de um arquivo inteiro e retorna hexdigest"""
    state = MD5State()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            md5_update(state, chunk)
    digest = md5_final(state)
    return digest.hex()
