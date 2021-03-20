from AesEverywhere import aes256

# encryption
encrypted = aes256.encrypt('1234567', 'E@gleM0BileP@ss')
print(encrypted)

# decryption
print(aes256.decrypt(encrypted, 'E@gleM0BileP@ss'))