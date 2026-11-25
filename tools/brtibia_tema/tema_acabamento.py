# Acabamento do tema marinho: cantos arredondados + moldura neon nas janelas/paineis,
# contorno discreto e cantos arredondados nos botoes; PvP/modos com contorno aceso quando ligados.
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
T = sys.argv[1]  # pasta do tema (contem images/...)
NEON = (46, 128, 255); DISCRETO = (44, 74, 130)
def mascara_rr(w, h, rect, r, largura=None, k=4):
    m = Image.new('L', (w*k, h*k), 0); d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = rect
    box = [x0*k, y0*k, (x1+1)*k-1, (y1+1)*k-1]
    if largura is None: d.rounded_rectangle(box, r*k, fill=255)
    else: d.rounded_rectangle(box, r*k, outline=255, width=largura*k)
    return np.asarray(m.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0
def processa(caminho, quadros, r, cor, brilho=True, contorno=True, forte=1.0):
    p = os.path.join(T, 'images', caminho)
    if not os.path.exists(p): print('falta', caminho); return
    im = Image.open(p).convert('RGBA'); x = np.asarray(im).astype(np.float32) / 255.0
    H, W = x.shape[:2]
    for (qx, qy, qw, qh, rect_rel, cor_q) in quadros:
        sub = x[qy:qy+qh, qx:qx+qw]
        h, w = sub.shape[:2]
        rx0, ry0, rx1, ry1 = rect_rel  # retangulo (pode sair do quadro p/ nao desenhar um lado)
        # cantos arredondados (alpha)
        m = mascara_rr(w + 40, h + 40, (rx0+20, ry0+20, rx1+20, ry1+20), r)[20:20+h, 20:20+w]
        sub[..., 3] *= m
        if contorno:
            lin = mascara_rr(w + 40, h + 40, (rx0+20, ry0+20, rx1+20, ry1+20), r, 1)[20:20+h, 20:20+w] * forte
            if brilho:
                gl = np.asarray(Image.fromarray((lin*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32)/255.0
                interno = mascara_rr(w + 40, h + 40, (rx0+21, ry0+21, rx1+19, ry1+19), max(r-1, 1))[20:20+h, 20:20+w]
                lin = np.maximum(lin, gl * 0.6 * interno)
            c = np.array(cor_q, np.float32) / 255.0
            sub[..., :3] = sub[..., :3] * (1 - lin[..., None]) + c * lin[..., None]
        x[qy:qy+qh, qx:qx+qw] = sub
    Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(p)
def degrade(caminho, topo=1.22, base=0.85, sombra=0.35, larg=6, faixa=None):
    # luz vinda de cima (mais claro em cima) + sombra interna junto da moldura (profundidade)
    p = os.path.join(T, 'images', caminho)
    if not os.path.exists(p): return
    x = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32) / 255.0
    h, w = x.shape[:2]
    y0, y1 = (0, h) if faixa is None else faixa
    hh = y1 - y0
    t = np.linspace(topo, base, hh, dtype=np.float32)[:, None, None]
    x[y0:y1, :, :3] *= t
    if sombra > 0:
        yy, xx = np.mgrid[0:hh, 0:w]
        d = np.minimum(np.minimum(yy, hh - 1 - yy), np.minimum(xx, w - 1 - xx)).astype(np.float32)
        s_ = 1 - sombra * np.clip(1 - (d - 2) / larg, 0, 1)
        x[y0:y1, :, :3] *= s_[..., None]
    Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(p)
def inteiro(w, h, r_cor=NEON): return [(0, 0, w, h, (0, 0, w-1, h-1), r_cor)]
def tam(c): return Image.open(os.path.join(T, 'images', c)).size
# degrades (antes dos contornos)
for c in ['ui/window.png', 'ui/window_new.png', 'ui/window-high.png', 'ui/window_headless.png', 'ui/popupwindow.png',
          'ui/2pixel_up_frame_borderimage.png', 'ui/miniwindow_body.png']:
    degrade(c, 1.30, 0.85, 0.35, 7)
degrade('ui/miniwindow_header.png', 1.45, 1.05, 0.0)         # barra de titulo um pouco mais clara
degrade('ui/panel_map.png', 1.0, 1.0, 0.45, 5)
degrade('ui/buttons.png', 1.35, 0.80, 0.0, faixa=(0, 20)); degrade('ui/buttons.png', 0.85, 1.15, 0.0, faixa=(20, 40))  # pressionado: luz invertida
degrade('game/combatmodes/onPanel.png', 1.35, 0.8, 0.0, faixa=(0, 20)); degrade('game/combatmodes/onPanel.png', 0.85, 1.15, 0.0, faixa=(20, 40))
degrade('ui/tabbutton_square.png', 1.35, 0.85, 0.0)
degrade('ui/console_button.png', 1.35, 0.85, 0.0)
# janelas e paineis grandes: neon com brilho
for c, r in [('ui/window.png', 6), ('ui/window_new.png', 6), ('ui/window-high.png', 6), ('ui/window_headless.png', 6),
             ('ui/popupwindow.png', 6), ('ui/2pixel_up_frame_borderimage.png', 3)]:
    try: w, h = tam(c)
    except Exception: print('falta', c); continue
    processa(c, inteiro(w, h), r, NEON)
# moldura do mapa: neon mais forte (2 passadas = linha mais viva e brilho maior)
w, h = tam('ui/panel_map.png'); processa('ui/panel_map.png', inteiro(w, h), 4, NEON); processa('ui/panel_map.png', inteiro(w, h), 4, (120, 180, 255), brilho=False, forte=0.6)
# mini-janelas: cabecalho (cantos de cima) + corpo (cantos de baixo), mesma moldura
w, h = tam('ui/miniwindow_header.png'); processa('ui/miniwindow_header.png', [(0, 0, w, h, (0, 0, w-1, h+8), NEON)], 4, NEON)
w, h = tam('ui/miniwindow_body.png');   processa('ui/miniwindow_body.png',   [(0, 0, w, h, (0, -10, w-1, h-1), NEON)], 4, NEON)
# botoes: cantos arredondados e contorno discreto; estado pressionado com contorno aceso
w, h = tam('ui/buttons.png'); processa('ui/buttons.png', [(0, 0, w, 20, (0, 0, w-1, 19), DISCRETO), (0, 20, w, 20, (0, 0, w-1, 19), NEON)], 3, None, brilho=False)
# PvP (2 estados 44x20) e modos de combate (2 estados 20x20): ligado = neon
w, h = tam('game/combatmodes/onPanel.png'); processa('game/combatmodes/onPanel.png', [(0, 0, w, 20, (0, 0, w-1, 19), DISCRETO), (0, 20, w, 20, (0, 0, w-1, 19), NEON)], 4, None, brilho=False)
for f in sorted(os.listdir(os.path.join(T, 'images/game/combatmodes'))):
    if f == 'onPanel.png' or not f.endswith('.png'): continue
    w, h = tam('game/combatmodes/' + f)
    if h >= 40: processa('game/combatmodes/' + f, [(0, 0, w, 20, (0, 0, w-1, 19), DISCRETO), (0, 20, w, 20, (0, 0, w-1, 19), NEON)], 3, None, brilho=False)
# botoes do inventario (grade 20x20 em 2 colunas: normal/ligado)
w, h = tam('inventory/buttons_general.png')
q = []
for y in range(0, h - 19, 20):
    q.append((0, y, 20, 20, (0, 0, 19, 19), DISCRETO)); q.append((20, y, 20, 20, (0, 0, 19, 19), NEON))
processa('inventory/buttons_general.png', q, 3, None, brilho=False)
print('acabamento ok')
# botoes do painel principal (40x20 = normal | pressionado)
pasta = os.path.join(T, 'images/options')
if os.path.isdir(pasta):
    for f in sorted(os.listdir(pasta)):
        if not f.endswith('.png'): continue
        w, h = tam('options/' + f)
        if (w, h) == (40, 20):
            processa('options/' + f, [(0, 0, 20, 20, (0, 0, 19, 19), DISCRETO), (20, 0, 20, 20, (0, 0, 19, 19), NEON)], 3, None, brilho=False)
print('opcoes ok')

# abas (chat e outras): cantos de cima arredondados; aba selecionada com contorno aceso
w, h = tam('ui/tabbutton_square.png')
processa('ui/tabbutton_square.png', [(0, 0, w, 18, (0, 0, w-1, 24), DISCRETO), (0, 18, w, 18, (0, 0, w-1, 24), DISCRETO), (0, 36, w, h-36, (0, 0, w-1, 26), NEON)], 3, None, brilho=False)
w, h = tam('ui/console_button.png')
processa('ui/console_button.png', [(0, 0, w, 18, (0, 0, w-1, 24), NEON), (0, 18, w, 18, (0, 0, w-1, 24), DISCRETO)], 3, None, brilho=False)
# moldura da area de texto do chat e de outras caixas: cantos arredondados, linha discreta
w, h = tam('ui/3pixel_frame_borderimage.png'); processa('ui/3pixel_frame_borderimage.png', inteiro(w, h, DISCRETO), 3, None, brilho=False)
print('abas ok')

# botao de leitura do chat (olho) e icones do console
w, h = tam('game/console/readOnly.png'); processa('game/console/readOnly.png', inteiro(w, h, DISCRETO), 3, None, brilho=False)
print('console ok')

# barras de vida/mana: brilho "vidro" (faixa clara em cima, base um pouco mais escura)
import glob as _g
def vidro(caminho):
    p = os.path.join(T, 'images', caminho)
    x = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32) / 255.0
    h = x.shape[0]
    t = np.linspace(0, 1, h, dtype=np.float32)
    perfil = np.where(t < 0.45, 1.30 - 0.3 * (t / 0.45), 1.0 - 0.18 * ((t - 0.45) / 0.55))
    x[..., :3] *= perfil[:, None, None]
    faixa = np.exp(-((t - 0.22) / 0.10) ** 2) * 0.22          # reflexo fino
    x[..., :3] = x[..., :3] + (1 - x[..., :3]) * faixa[:, None, None]
    Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(p)
for f in ['healthmana/hitpoints_bar_filled.png', 'healthmana/mana_bar_filled.png'] + \
         [os.path.relpath(q, os.path.join(T, 'images')) for q in _g.glob(os.path.join(T, 'images/bars/horizontal_*progressbar*.png'))]:
    if os.path.exists(os.path.join(T, 'images', f)): vidro(f)
print('barras ok')
