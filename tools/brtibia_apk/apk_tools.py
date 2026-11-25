# Ferramentas para remontar, alinhar e assinar (v2) um APK sem o Android SDK.
# Uso:
#   python3 apk_tools.py alinhar entrada.apk saida.apk [--sem-assinatura] [--trocar caminho_no_apk=arquivo_local ...]
#   python3 apk_tools.py assinar_v2 entrada.apk saida.apk chave.p12 senha.txt
import sys, struct, zlib, hashlib, os

def ler_zip(data):
    eocd = data.rfind(b'PK\x05\x06')
    if eocd < 0:
        raise SystemExit('EOCD nao encontrado')
    n_total, cd_size, cd_off = struct.unpack_from('<HII', data, eocd + 10)
    entradas = []
    p = cd_off
    for _ in range(n_total):
        assert data[p:p+4] == b'PK\x01\x02'
        (ver_made, ver_need, flags, metodo, mtime, mdate, crc, csize, usize, nlen, xlen, clen,
         disk, iattr, eattr, loff) = struct.unpack_from('<HHHHHHIIIHHHHHII', data, p + 4)
        nome = data[p+46:p+46+nlen]
        extra_cd = data[p+46+nlen:p+46+nlen+xlen]
        coment = data[p+46+nlen+xlen:p+46+nlen+xlen+clen]
        # dados brutos (comprimidos) a partir do cabecalho local
        assert data[loff:loff+4] == b'PK\x03\x04'
        lnlen, lxlen = struct.unpack_from('<HH', data, loff + 26)
        ini = loff + 30 + lnlen + lxlen
        bruto = data[ini:ini+csize]
        entradas.append(dict(nome=nome, ver_made=ver_made, ver_need=ver_need, flags=flags & ~0x0008,
                             metodo=metodo, mtime=mtime, mdate=mdate, crc=crc, csize=csize, usize=usize,
                             extra_cd=extra_cd, coment=coment, iattr=iattr, eattr=eattr, bruto=bruto))
        p += 46 + nlen + xlen + clen
    return entradas, cd_off, cd_size, eocd

def escrever_zip(entradas):
    out = bytearray(); cd = bytearray()
    for e in entradas:
        nome = e['nome']
        alin = 0
        if e['metodo'] == 0:
            alin = 16384 if nome.endswith(b'.so') else 4
        base = len(out) + 30 + len(nome)
        pad = (-base) % alin if alin else 0
        extra = b''
        if pad:
            # campo extra de alinhamento (id 0xD935, como o zipalign do Android)
            if pad < 6:
                pad += alin
            extra = struct.pack('<HH', 0xD935, pad - 4) + struct.pack('<H', alin) + b'\x00' * (pad - 6)
        loff = len(out)
        out += struct.pack('<IHHHHHIIIHH', 0x04034b50, e['ver_need'], e['flags'], e['metodo'], e['mtime'],
                           e['mdate'], e['crc'], e['csize'], e['usize'], len(nome), len(extra))
        out += nome + extra + e['bruto']
        cd += struct.pack('<IHHHHHHIIIHHHHHII', 0x02014b50, e['ver_made'], e['ver_need'], e['flags'], e['metodo'],
                          e['mtime'], e['mdate'], e['crc'], e['csize'], e['usize'], len(nome), 0, len(e['coment']),
                          0, e['iattr'], e['eattr'], loff)
        cd += nome + e['coment']
    cd_off = len(out)
    out += cd
    out += struct.pack('<IHHHHIIH', 0x06054b50, 0, 0, len(entradas), len(entradas), len(cd), cd_off, 0)
    return bytes(out)

def entrada_de_arquivo(nome, caminho, modelo=None, armazenar=False):
    dados = open(caminho, 'rb').read()
    crc = zlib.crc32(dados) & 0xffffffff
    if armazenar:
        bruto, metodo = dados, 0
    else:
        c = zlib.compressobj(9, zlib.DEFLATED, -15)
        bruto, metodo = c.compress(dados) + c.flush(), 8
    e = dict(modelo) if modelo else dict(ver_made=20, ver_need=20, flags=0, mtime=0, mdate=0x21, extra_cd=b'',
                                         coment=b'', iattr=0, eattr=0)
    e.update(nome=nome, metodo=metodo, crc=crc, csize=len(bruto), usize=len(dados), bruto=bruto)
    if metodo == 8:
        e['ver_need'] = max(e.get('ver_need', 20), 20)
    return e

def alinhar(ent, sai, args):
    data = open(ent, 'rb').read()
    entradas, *_ = ler_zip(data)
    sem_ass = '--sem-assinatura' in args
    trocas = dict(a.split('=', 1) for a in args if '=' in a)
    novas = []
    for e in entradas:
        n = e['nome'].decode()
        if sem_ass and n.startswith('META-INF/') and (n.endswith(('.SF', '.RSA', '.DSA', '.EC')) or n == 'META-INF/MANIFEST.MF'):
            continue
        if n in trocas:
            e = entrada_de_arquivo(e['nome'], trocas.pop(n), e, armazenar=(e['metodo'] == 0))
        novas.append(e)
    for n, c in trocas.items():
        novas.append(entrada_de_arquivo(n.encode(), c))
    open(sai, 'wb').write(escrever_zip(novas))
    print('ok', sai, len(novas), 'entradas')

# ---------------- assinatura v2 ----------------
def lp(b):
    return struct.pack('<I', len(b)) + b

def digest_chunked(secoes):
    dig = []
    for s in secoes:
        for i in range(0, len(s), 1 << 20):
            ch = s[i:i + (1 << 20)]
            dig.append(hashlib.sha256(b'\xa5' + struct.pack('<I', len(ch)) + ch).digest())
    return hashlib.sha256(b'\x5a' + struct.pack('<I', len(dig)) + b''.join(dig)).digest()

def assinar_v2(ent, sai, p12, senha_arq):
    from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PublicFormat
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    senha = open(senha_arq, 'rb').read().strip()
    chave, cert, _ = pkcs12.load_key_and_certificates(open(p12, 'rb').read(), senha)
    data = open(ent, 'rb').read()
    _, cd_off, cd_size, eocd = ler_zip(data)
    conteudo, cd, fim = data[:cd_off], data[cd_off:cd_off + cd_size], bytearray(data[cd_off + cd_size:])
    assert cd_off + cd_size == eocd
    fim_dig = bytearray(fim); struct.pack_into('<I', fim_dig, 16, cd_off)
    ALG = 0x0103  # RSASSA-PKCS1-v1_5 com SHA-256
    digest = digest_chunked([conteudo, cd, bytes(fim_dig)])
    cert_der = cert.public_bytes(Encoding.DER)
    signed = lp(lp(struct.pack('<I', ALG) + lp(digest))) + lp(lp(cert_der)) + lp(b'')
    assin = chave.sign(signed, padding.PKCS1v15(), hashes.SHA256())
    pub = chave.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
    signer = lp(signed) + lp(lp(struct.pack('<I', ALG) + lp(assin))) + lp(pub)
    valor = lp(lp(signer))
    par = struct.pack('<I', 0x7109871a) + valor
    corpo = struct.pack('<Q', len(par)) + par
    tam = len(corpo) + 8 + 16
    bloco = struct.pack('<Q', tam) + corpo + struct.pack('<Q', tam) + b'APK Sig Block 42'
    struct.pack_into('<I', fim, 16, cd_off + len(bloco))
    open(sai, 'wb').write(conteudo + bloco + cd + bytes(fim))
    print('assinado (v2)', sai)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'alinhar':
        alinhar(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif cmd == 'assinar_v2':
        assinar_v2(*sys.argv[2:6])
