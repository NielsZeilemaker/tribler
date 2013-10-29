from Crypto.PublicKey import RSA
from Crypto.Random.random import StrongRandom
from Crypto.Util.number import GCD, bytes_to_long, long_to_bytes

from gmpy import mpz

from hashlib import sha1

from time import time
from random import randint
from collections import namedtuple
from struct import pack, unpack, unpack_from
import json

RSAKey = namedtuple('RSAKey', ['n', 'e', 'p', 'q', 'd', 'size'])

def rsa_init(bits=1024):
    key = RSA.generate(bits)
    return RSAKey(mpz(key.key.n), mpz(key.key.e), mpz(key.key.p), mpz(key.key.q), mpz(key.key.d), bits)

def rsa_compatible(n, phi):
    phi = long(phi)
    while True:
        e = StrongRandom().randint(1, phi - 1)
        if GCD(e, phi) == 1: break
    return RSAKey(mpz(n), mpz(e), None, None, None, 1024)

def rsa_encrypt(key, element):
    assert isinstance(element, (long, int)), type(element)

    _element = mpz(element)
    return long(pow(_element, key.e, key.n))

def rsa_decrypt(key, cipher):
    assert isinstance(cipher, long), type(cipher)

    _cipher = mpz(cipher)
    return long(pow(_cipher, key.d, key.n))

def hash_element(element):
    return sha1(str(element)).digest()

def get_bits(number):
    bits = 0
    while number > 2 ** bits:
        bits += 1
    return bits

def key_to_bytes(key):
    keydict = key.__dict__.copy()
    non_mpzdict = {}
    for key, value in keydict.items():
        if value:
            non_mpzdict[key] = long(value)

    return json.dumps(non_mpzdict)

def bytes_to_key(bytes):
    keydict = json.loads(bytes)
    return RSAKey(mpz(keydict['n']), mpz(keydict['e']), mpz(keydict['p']) if 'p' in keydict else None, mpz(keydict['q'])  if 'q' in keydict else None, mpz(keydict['d'])  if 'd' in keydict else None, keydict['size'])

if __name__ == "__main__":
    MAXLONG128 = (1 << 1024) - 1

    # lets check if this rsa thing works
    key = rsa_init(1024)
    serialized_key = bytes_to_key(key_to_bytes(key))

    assert key.n == serialized_key.n, (key.n, serialized_key.n)
    assert key.e == serialized_key.e, (key.e, serialized_key.e)
    assert key.p == serialized_key.p, (key.p, serialized_key.p)
    assert key.q == serialized_key.q, (key.q, serialized_key.q)
    assert key.d == serialized_key.d, (key.d, serialized_key.d)
    assert key.size == serialized_key.size

    encrypted0 = rsa_encrypt(key, 0l)
    encrypted1 = rsa_encrypt(key, 1l)
    assert encrypted0 < MAXLONG128
    assert encrypted1 < MAXLONG128

    test = rsa_decrypt(key, encrypted0)
    assert test == 0l, test

    test = rsa_decrypt(key, encrypted1)
    assert test == 1l, test

    comp_key = rsa_compatible(key.n, key.n / 2)
    compencrypted0 = rsa_encrypt(comp_key, 0l)
    compencrypted1 = rsa_encrypt(comp_key, 1l)
    assert compencrypted0 < MAXLONG128
    assert compencrypted1 < MAXLONG128

    twiceencrypted0 = rsa_encrypt(comp_key, encrypted0)
    twiceencrypted1 = rsa_encrypt(comp_key, encrypted1)
    assert twiceencrypted0 < MAXLONG128
    assert twiceencrypted1 < MAXLONG128

    assert compencrypted0 == rsa_decrypt(key, twiceencrypted0)
    assert compencrypted1 == rsa_decrypt(key, twiceencrypted1)

    hcompencrypted0 = hash_element(compencrypted0)
    hcompecnrypted1 = hash_element(compencrypted1)
    assert isinstance(hcompencrypted0, str) and len(hcompencrypted0) == 20
    assert isinstance(hcompecnrypted1, str) and len(hcompecnrypted1) == 20

    assert hcompencrypted0 == hash_element(rsa_decrypt(key, twiceencrypted0))
    assert hcompecnrypted1 == hash_element(rsa_decrypt(key, twiceencrypted1))

    fakeinfohash = '296069              '
    assert long_to_bytes(rsa_decrypt(key, rsa_encrypt(key, bytes_to_long(fakeinfohash)))) == fakeinfohash

    # performance
    random_list = [randint(0, i * 1000) for i in xrange(100)]

    t1 = time()
    encrypted_values = []
    for i, value in enumerate(random_list):
        encrypted_values.append(rsa_encrypt(key, value))

    t2 = time()
    for cipher in encrypted_values:
        rsa_decrypt(key, cipher)

    print "Encrypting took", t2 - t1
    print "Decrypting took", time() - t2
