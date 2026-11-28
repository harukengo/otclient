# Tema BRTibia "azul marinho + neon" (v2)
# - fundo liso bem escuro, sem o granulado de pedra
# - neon com hierarquia: forte so na moldura externa das janelas/paineis grandes,
#   linha fina e apagada nas divisoes internas e em pecas pequenas (botoes, slots)
# - uma linha so por chanfro (so o lado claro do relevo vira linha)
# - icones, setas e textos claros dentro das imagens sao preservados
# - botoes um pouco mais claros que os paineis, com realce em cima (volume)
import sys, os, numpy as np, cv2
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
BASE = np.array([13, 19, 36], np.float32) / 255.0       # #0D1324 (v3: um pouco mais claro, mais contraste)
BOTAO = np.array([26, 39, 72], np.float32) / 255.0
NEON = np.array([46, 128, 255], np.float32) / 255.0
LINHA = np.array([52, 86, 150], np.float32) / 255.0      # divisao interna (v3: mais visivel)
CLARO = np.array([0.82, 0.88, 1.0], np.float32)          # tom dos detalhes claros (icones/setas)
n = 0
for raiz, _, arqs in os.walk(src):
    for a in arqs:
        if not a.lower().endswith('.png'): continue
        p = os.path.join(raiz, a); rel_p = os.path.relpath(p, src); q = os.path.join(dst, rel_p)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        x = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32) / 255.0
        h, w = x.shape[:2]
        rgb = x[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        peso = np.clip((0.30 - sat) / 0.12, 0, 1)
        lum = (0.299*rgb[..., 0] + 0.587*rgb[..., 1] + 0.114*rgb[..., 2]).astype(np.float32)
        liso = lum
        if min(h, w) >= 6:
            for _ in range(3):
                liso = cv2.bilateralFilter(liso, 7, 0.10, 4)
        sel = (peso > 0.5) & (x[..., 3] > 0.5)
        media = float(np.median(liso[sel])) if sel.any() else 0.3
        r = np.clip(liso / max(media, 1e-3), 0, 4)
        nome = a.lower()
        if 'slot' in nome or nome.startswith('inventory_'):
            tint = np.array([0.55, 0.68, 1.0], np.float32)
            novo = np.clip(lum[..., None] * 0.95 * tint + 0.025, 0, 1)   # v3: slots mais claros (itens escuros aparecem)
            wgt = peso[..., None]
            x[..., :3] = rgb * (1 - wgt) + novo * wgt
            Image.fromarray((x * 255 + 0.5).astype(np.uint8), 'RGBA').save(q); n += 1
            continue
        botao = ('button' in nome or 'botao' in nome)
        cor_base = BOTAO if botao else BASE
        fundo = np.clip(r ** 0.6, 0, 1.6)[..., None] * cor_base
        if botao:  # volume: um pouco mais claro em cima de cada faixa de 20 px (estados empilhados)
            yy = (np.arange(h) % 20) / 19.0 if h >= 20 else np.arange(h) / max(h - 1, 1)
            fundo = fundo * (1.25 - 0.4 * yy)[:, None, None]
        # detalhes bem mais claros que a media (setas, icones, marcas) ficam claros
        hl = np.clip((r - 1.5) / 0.8, 0, 1)[..., None]
        fundo = fundo * (1 - hl) + (lum[..., None] * CLARO) * hl
        # chanfros viram uma linha discreta (o neon das separacoes grandes e desenhado pelo cliente)
        l8 = np.clip(liso * 255, 0, 255).astype(np.uint8)
        e = cv2.Canny(l8, 40, 90, L2gradient=True).astype(np.float32) / 255.0 if min(h, w) >= 4 else np.zeros((h, w), np.float32)
        e = e * (1 - hl[..., 0]) * 0.55
        if any(k in nome for k in ('background', 'flat', 'textedit')):  # texturas repetidas: sem linhas
            e = e * 0
        cor = fundo * (1 - e[..., None]) + LINHA * e[..., None]
        wgt = peso[..., None]
        x[..., :3] = rgb * (1 - wgt) + np.clip(cor, 0, 1) * wgt
        Image.fromarray((x * 255 + 0.5).astype(np.uint8), 'RGBA').save(q); n += 1
print('imagens', n)
