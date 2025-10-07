from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Şifreleme Fonksiyonları ---
def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char
    return result

def caesar_decrypt(text, shift):
    return caesar_encrypt(text, -shift)

def vigenere_encrypt(text, key):
    result = ""
    key = key.lower()
    key_indices = [ord(k) - ord('a') for k in key]
    ki = 0
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shift = key_indices[ki % len(key)]
            result += chr((ord(char) - base + shift) % 26 + base)
            ki += 1
        else:
            result += char
    return result

def vigenere_decrypt(text, key):
    result = ""
    key = key.lower()
    key_indices = [ord(k) - ord('a') for k in key]
    ki = 0
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shift = key_indices[ki % len(key)]
            result += chr((ord(char) - base - shift) % 26 + base)
            ki += 1
        else:
            result += char
    return result

def substitution_encrypt(text, key):
    key_map = {}
    alphabet_upper = [chr(i) for i in range(65, 91)]
    alphabet_lower = [chr(i) for i in range(97, 123)]
    for i, k in enumerate(key.upper()):
        key_map[alphabet_upper[i]] = k
        key_map[alphabet_lower[i]] = k.lower()
    result = ""
    for char in text:
        if char.isalpha():
            result += key_map.get(char, char)
        else:
            result += char
    return result

def substitution_decrypt(text, key):
    reverse_map = {}
    alphabet_upper = [chr(i) for i in range(65, 91)]
    alphabet_lower = [chr(i) for i in range(97, 123)]
    for i, k in enumerate(key.upper()):
        reverse_map[k] = alphabet_upper[i]
        reverse_map[k.lower()] = alphabet_lower[i]
    result = ""
    for char in text:
        if char.isalpha():
            result += reverse_map.get(char, char)
        else:
            result += char
    return result

def modinv(a, m=26):
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return None

def affine_encrypt(text, a, b):
    result = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            x = ord(char) - base
            enc = (a * x + b) % 26
            result += chr(enc + base)
        else:
            result += char
    return result

def affine_decrypt(text, a, b):
    result = ""
    a_inv = modinv(a)
    if a_inv is None:
        return "Hata: 'a' sayısının mod 26 tersini hesaplanamadı."
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            y = ord(char) - base
            dec = (a_inv * (y - b)) % 26
            result += chr(dec + base)
        else:
            result += char
    return result

# --- Global değişkenler ---
stored_encrypted_text = ""
stored_method = ""
stored_keys = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    global stored_encrypted_text, stored_method, stored_keys
    data = request.json
    text = data.get('text', '')
    method = data.get('method', '')
    key = data.get('key', '')
    a = data.get('a')
    b = data.get('b')

    try:
        if method == 'caesar':
            shift = int(key) if key else 3
            result = caesar_encrypt(text, shift)
            stored_keys = {"key": key}
        elif method == 'vigenere':
            if not key:
                return jsonify({'error': 'Vigenere için anahtar gerekli'}), 400
            result = vigenere_encrypt(text, key)
            stored_keys = {"key": key}
        elif method == 'substitution':
            if not key or len(key) != 26:
                return jsonify({'error': 'Substitution için 26 harfli anahtar gerekli'}), 400
            result = substitution_encrypt(text, key)
            stored_keys = {"key": key}
        elif method == 'affine':
            a = int(a)
            b = int(b)
            result = affine_encrypt(text, a, b)
            stored_keys = {"a": a, "b": b}
        else:
            return jsonify({'error': 'Geçersiz şifreleme yöntemi'}), 400

        stored_encrypted_text = result
        stored_method = method

        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/decrypt', methods=['POST'])
def decrypt():
    global stored_encrypted_text, stored_method, stored_keys
    data = request.json
    key = data.get('key', '')
    a = data.get('a')
    b = data.get('b')

    try:
        if stored_method == "caesar":
            if key != stored_keys.get("key", ""):
                return jsonify({'error': 'Yanlış anahtar'}), 403
            result = caesar_decrypt(stored_encrypted_text, int(key))
        elif stored_method == "vigenere":
            if key != stored_keys.get("key", ""):
                return jsonify({'error': 'Yanlış anahtar'}), 403
            result = vigenere_decrypt(stored_encrypted_text, key)
        elif stored_method == "substitution":
            if key != stored_keys.get("key", ""):
                return jsonify({'error': 'Yanlış anahtar'}), 403
            result = substitution_decrypt(stored_encrypted_text, key)
        elif stored_method == "affine":
            if str(a) != str(stored_keys.get("a")) or str(b) != str(stored_keys.get("b")):
                return jsonify({'error': 'Yanlış anahtar'}), 403
            result = affine_decrypt(stored_encrypted_text, int(a), int(b))
        else:
            return jsonify({'error': 'Geçersiz şifreleme yöntemi'}), 400

        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
