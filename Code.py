"""
MacondoBeat - Un juego de ritmo estilo Guitar Hero con sabor colombiano.
 
Controles:
    D, F, J, K -> golpear los 4 carriles
    ENTER      -> confirmar / jugar / reiniciar
    ESC        -> volver al menú
    Click en OPCIONES -> cambiar dificultad
    Click en MENÚ     -> mostrar/ocultar ayuda de controles
 
Los sonidos de cada carril se generan matemáticamente (estilo marimba del
Pacífico colombiano) así que el juego no necesita archivos de audio externos.
"""
 
import pygame
import numpy as np
import random
import math
import sys
 
# ----------------------------------------------------------------------
# INICIALIZACIÓN
# ----------------------------------------------------------------------
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.mixer.init()
 
ANCHO, ALTO = 800, 600
FPS = 60
 
# ----------------------------------------------------------------------
# COLORES (bandera de Colombia + paleta pastel "tierna")
# ----------------------------------------------------------------------
AMARILLO = (255, 205, 0)
AZUL = (0, 56, 147)
ROJO = (206, 17, 38)
BLANCO = (255, 255, 255)
NEGRO_SUAVE = (25, 15, 10)
 
FONDO_ARRIBA_INICIO = (60, 24, 18)     # atardecer caribeño
FONDO_ABAJO_INICIO = (18, 10, 8)
FONDO_ARRIBA_JUEGO = (35, 20, 40)      # noche mágica de Macondo
FONDO_ABAJO_JUEGO = (10, 8, 15)
 
COLORES_CARRIL = [
    (255, 214, 92),   # amarillo pastel
    (108, 201, 132),  # verde
    (94, 178, 235),   # azul cielo
    (235, 111, 105),  # rojo coral
]
COLORES_CARRIL_CLARO = [
    (255, 235, 170),
    (176, 232, 190),
    (178, 222, 245),
    (245, 175, 170),
]
 
CARRIL_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
CARRIL_LABELS = ["D", "F", "J", "K"]
NUM_CARRILES = 4
CARRIL_ANCHO = 90
CARRILES_X = [
    ANCHO // 2 - (NUM_CARRILES * CARRIL_ANCHO) // 2 + i * CARRIL_ANCHO
    for i in range(NUM_CARRILES)
]
HIT_Y = 500
NOTE_RADIO = 20
 
# ----------------------------------------------------------------------
# PANTALLA / RELOJ / FUENTES
# ----------------------------------------------------------------------
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("MacondoBeat")
reloj = pygame.time.Clock()
 
fuente_titulo = pygame.font.SysFont("comicsansms,arial", 60, bold=True)
fuente_subtitulo = pygame.font.SysFont("arial", 26, bold=True)
fuente_dato = pygame.font.SysFont("arial", 20)
fuente_boton = pygame.font.SysFont("arial", 20, bold=True)
fuente_hud = pygame.font.SysFont("arial", 24, bold=True)
fuente_juicio = pygame.font.SysFont("arial", 30, bold=True)
fuente_grande = pygame.font.SysFont("comicsansms,arial", 48, bold=True)
 
 
# ----------------------------------------------------------------------
# SONIDO: generación tipo marimba (percusivo, decae rápido)
# ----------------------------------------------------------------------
def generar_tono(freq, duracion=0.35, volumen=0.5):
    sample_rate = 44100
    n = int(sample_rate * duracion)
    t = np.linspace(0, duracion, n, False)
    onda = (
        np.sin(2 * np.pi * freq * t)
        + 0.5 * np.sin(2 * np.pi * freq * 2 * t)
        + 0.25 * np.sin(2 * np.pi * freq * 4 * t)
    )
    envolvente = np.exp(-6 * t)
    onda = onda * envolvente
    onda = onda / np.max(np.abs(onda))
    audio = (onda * volumen * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(audio)
 
 
# escala pentatónica mayor, alegre, tipo marimba de chonta
NOTAS_FRECUENCIA = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
try:
    SONIDOS_CARRIL = [generar_tono(f) for f in NOTAS_FRECUENCIA]
    SONIDO_FALLO = generar_tono(140, duracion=0.18, volumen=0.35)
    SONIDO_OK = True
except Exception:
    SONIDOS_CARRIL = [None, None, None, None]
    SONIDO_FALLO = None
    SONIDO_OK = False
 
 
def reproducir(sonido):
    if SONIDO_OK and sonido is not None:
        try:
            sonido.play()
        except Exception:
            pass
 
 
# ----------------------------------------------------------------------
# DATOS CURIOSOS SOBRE COLOMBIA (para la pantalla de inicio)
# ----------------------------------------------------------------------
DATOS_CURIOSOS = [
    "Colombia is the second most biodiverse country on Earth.",
    "Colombia is the only South American country with coastlines on both the Pacific and the Caribbean.",
    "Cumbia and vallenato are two of Colombia's most iconic musical genres.",
    "The fictional town of Macondo, invented by Gabriel Garcia Marquez, inspired this game's name.",
    "The wax palm, Colombia's national tree, is the tallest palm species in the world.",
    "Colombia is one of the world's largest producers of emeralds.",
    "Barranquilla's Carnival is one of the biggest carnivals on the planet.",
    "Colombian coffee from the 'Coffee Triangle' is famous worldwide for its smoothness.",
    "Bogota sits at roughly 2,640 meters above sea level, making it one of the highest capitals in the world.",
    "The marimba de chonta, a wooden xylophone, is central to Afro-Colombian Pacific music.",
]
 
# ----------------------------------------------------------------------
# DIFICULTADES
# ----------------------------------------------------------------------
DIFICULTADES = {
    "Facil": {"velocidad": 250, "bpm": 84, "perfecto": 110, "bien": 200},
    "Normal": {"velocidad": 320, "bpm": 100, "perfecto": 85, "bien": 165},
    "Dificil": {"velocidad": 400, "bpm": 118, "perfecto": 65, "bien": 130},
}
LISTA_DIFICULTADES = ["Facil", "Normal", "Dificil"]
dificultad_actual = "Normal"
 
# ----------------------------------------------------------------------
# FONDOS PRECALCULADOS (degradados)
# ----------------------------------------------------------------------
def crear_fondo_degradado(ancho, alto, color_arriba, color_abajo):
    superficie = pygame.Surface((ancho, alto))
    for y in range(alto):
        t = y / alto
        color = [
            int(color_arriba[i] + (color_abajo[i] - color_arriba[i]) * t)
            for i in range(3)
        ]
        pygame.draw.line(superficie, color, (0, y), (ancho, y))
    return superficie
 
 
FONDO_INICIO = crear_fondo_degradado(ANCHO, ALTO, FONDO_ARRIBA_INICIO, FONDO_ABAJO_INICIO)
FONDO_JUEGO = crear_fondo_degradado(ANCHO, ALTO, FONDO_ARRIBA_JUEGO, FONDO_ABAJO_JUEGO)
 
 
# ----------------------------------------------------------------------
# UTILIDADES DE DIBUJO
# ----------------------------------------------------------------------
def render_texto_outline(fuente, texto, color_texto, color_borde, grosor=3):
    base = fuente.render(texto, True, color_texto)
    tam = (base.get_width() + grosor * 2, base.get_height() + grosor * 2)
    superficie = pygame.Surface(tam, pygame.SRCALPHA)
    borde = fuente.render(texto, True, color_borde)
    for dx in range(-grosor, grosor + 1):
        for dy in range(-grosor, grosor + 1):
            if dx * dx + dy * dy <= grosor * grosor and (dx, dy) != (0, 0):
                superficie.blit(borde, (grosor + dx, grosor + dy))
    superficie.blit(base, (grosor, grosor))
    return superficie
 
 
def dibujar_nota_icono(superficie, x, y, color, escala=1.0, borde=NEGRO_SUAVE):
    r = max(3, int(NOTE_RADIO * 0.62 * escala))
    pygame.draw.circle(superficie, color, (int(x), int(y)), r)
    pygame.draw.circle(superficie, borde, (int(x), int(y)), r, max(1, int(2 * escala)))
    # brillo tierno
    pygame.draw.circle(
        superficie, BLANCO, (int(x - r * 0.35), int(y - r * 0.35)), max(1, int(r * 0.28))
    )
    alto_palo = int(24 * escala)
    px = x + r - 2
    pygame.draw.line(superficie, borde, (px, y), (px, y - alto_palo), max(2, int(3 * escala)))
    puntos = [
        (px, y - alto_palo),
        (px + 11 * escala, y - alto_palo + 7 * escala),
        (px + 9 * escala, y - alto_palo + 15 * escala),
        (px, y - alto_palo + 11 * escala),
    ]
    pygame.draw.polygon(superficie, borde, puntos)
 
 
def dibujar_palmera(superficie, x, y, tiempo, escala=1.0, color_hojas=(90, 200, 110)):
    balanceo = math.sin(tiempo * 1.6) * 6
    # tronco
    pygame.draw.line(
        superficie, (120, 80, 50), (x, y), (x + balanceo * 0.3, y - 46 * escala), int(7 * escala)
    )
    copa_x = x + balanceo * 0.3
    copa_y = y - 46 * escala
    for i in range(5):
        angulo = math.radians(-90 + (i - 2) * 32 + balanceo)
        largo = 26 * escala
        fx = copa_x + math.cos(angulo) * largo
        fy = copa_y + math.sin(angulo) * largo
        pygame.draw.line(superficie, color_hojas, (copa_x, copa_y), (fx, fy), int(6 * escala))
    pygame.draw.circle(superficie, (110, 70, 40), (int(copa_x), int(copa_y)), int(5 * escala))
 
 
def dibujar_boton(superficie, rect, texto, activo=False):
    color_fondo = (255, 255, 255, 40) if not activo else (255, 205, 0, 90)
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, color_fondo, s.get_rect(), border_radius=10)
    pygame.draw.rect(s, BLANCO, s.get_rect(), 2, border_radius=10)
    superficie.blit(s, rect.topleft)
    txt = fuente_boton.render(texto, True, BLANCO)
    superficie.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
 
 
# ----------------------------------------------------------------------
# PARTÍCULAS DE CONFETI (al acertar una nota)
# ----------------------------------------------------------------------
class Particula:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        angulo = random.uniform(0, 2 * math.pi)
        vel = random.uniform(90, 230)
        self.vx = math.cos(angulo) * vel
        self.vy = math.sin(angulo) * vel - 120
        self.color = color
        self.vida = 0.55
        self.edad = 0.0
        self.tam = random.uniform(3, 6)
 
    def actualizar(self, dt):
        self.edad += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 340 * dt
        return self.edad < self.vida
 
    def dibujar(self, superficie):
        alpha = max(0, int(255 * (1 - self.edad / self.vida)))
        s = pygame.Surface((self.tam * 2, self.tam * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.tam, self.tam), self.tam)
        superficie.blit(s, (self.x - self.tam, self.y - self.tam))
 
 
particulas = []
 
 
# ----------------------------------------------------------------------
# GENERACIÓN DE LA "CANCIÓN" (patrón rítmico tipo cumbia/currulao)
# ----------------------------------------------------------------------
def generar_chart(duracion_ms, bpm):
    paso_ms = 60000 / bpm / 2  # corchea
    patrones = [
        [0, 2, None, 1, None, 3, 1, None],
        [1, None, 0, None, 2, 3, None, 0],
        [3, 1, None, 0, 2, None, 1, None],
        [0, None, 3, 2, None, 1, 0, None],
        [2, 0, 1, None, 3, None, 2, None],
    ]
    eventos = []
    t = 2200.0
    while t < duracion_ms:
        patron = random.choice(patrones)
        for paso in patron:
            if t >= duracion_ms:
                break
            if paso is not None:
                eventos.append({"t": t, "carril": paso, "juzgada": False, "resultado": None})
            t += paso_ms
    return eventos
 
 
# ----------------------------------------------------------------------
# ESTADO DEL JUEGO
# ----------------------------------------------------------------------
estado = "INICIO"
mostrar_ayuda = False
dato_indice = 0
dato_alpha = 255
dato_temporizador = 0.0
 
chart = []
tiempo_inicio_juego = 0
tiempo_juego_actual = 0
duracion_cancion_ms = 60000
 
puntaje = 0
combo = 0
mejor_combo = 0
conteo = {"Perfecto": 0, "Bien": 0, "Fallo": 0}
juicio_texto = ""
juicio_timer = 0.0
juicio_color = BLANCO
combo_pop = 0.0  # animación de "pop" cuando sube el combo
 
flash_carril = [0.0, 0.0, 0.0, 0.0]  # brillo del carril al presionar tecla
 
 
def iniciar_juego():
    global chart, tiempo_inicio_juego, puntaje, combo, mejor_combo
    global conteo, particulas, estado, duracion_cancion_ms
    cfg = DIFICULTADES[dificultad_actual]
    duracion_cancion_ms = 46000
    chart = generar_chart(duracion_cancion_ms, cfg["bpm"])
    tiempo_inicio_juego = pygame.time.get_ticks()
    puntaje = 0
    combo = 0
    mejor_combo = 0
    conteo = {"Perfecto": 0, "Bien": 0, "Fallo": 0}
    particulas = []
    estado = "JUEGO"
 
 
def mostrar_juicio(texto, color):
    global juicio_texto, juicio_timer, juicio_color
    juicio_texto = texto
    juicio_color = color
    juicio_timer = 0.5
 
 
# rects de botones de la pantalla de inicio
rect_menu = pygame.Rect(ANCHO // 2 - 140, 410, 120, 34)
rect_opciones = pygame.Rect(ANCHO // 2 + 20, 410, 120, 34)
 
corriendo = True
while corriendo:
    dt = reloj.tick(FPS) / 1000.0
 
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            corriendo = False
 
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if estado == "INICIO":
                if rect_menu.collidepoint(evento.pos):
                    mostrar_ayuda = not mostrar_ayuda
                elif rect_opciones.collidepoint(evento.pos):
                    idx = LISTA_DIFICULTADES.index(dificultad_actual)
                    dificultad_actual = LISTA_DIFICULTADES[(idx + 1) % len(LISTA_DIFICULTADES)]
 
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                if estado in ("JUEGO", "FIN"):
                    estado = "INICIO"
 
            if estado == "INICIO" and evento.key == pygame.K_RETURN:
                iniciar_juego()
 
            elif estado == "JUEGO" and evento.key in CARRIL_KEYS:
                carril = CARRIL_KEYS.index(evento.key)
                flash_carril[carril] = 1.0
                cfg = DIFICULTADES[dificultad_actual]
                ventana_total = cfg["bien"] + 40
 
                candidata = None
                menor_diff = None
                for ev in chart:
                    if ev["carril"] != carril or ev["juzgada"]:
                        continue
                    diff = abs(ev["t"] - tiempo_juego_actual)
                    if diff <= ventana_total and (menor_diff is None or diff < menor_diff):
                        candidata = ev
                        menor_diff = diff
 
                if candidata is not None:
                    candidata["juzgada"] = True
                    if menor_diff <= cfg["perfecto"]:
                        candidata["resultado"] = "Perfecto"
                        puntaje += 100 + combo * 2
                        conteo["Perfecto"] += 1
                        combo += 1
                        combo_pop = 0.25
                        mostrar_juicio("PERFECTO!", AMARILLO)
                    else:
                        candidata["resultado"] = "Bien"
                        puntaje += 50 + combo
                        conteo["Bien"] += 1
                        combo += 1
                        combo_pop = 0.18
                        mostrar_juicio("BIEN", COLORES_CARRIL[2])
 
                    mejor_combo = max(mejor_combo, combo)
                    cx = CARRILES_X[carril] + CARRIL_ANCHO // 2
                    for _ in range(14):
                        particulas.append(
                            Particula(cx, HIT_Y, random.choice([AMARILLO, AZUL, ROJO, BLANCO]))
                        )
                    reproducir(SONIDOS_CARRIL[carril])
                else:
                    combo = 0
                    mostrar_juicio("...", (150, 150, 150))
 
            elif estado == "FIN" and evento.key == pygame.K_RETURN:
                iniciar_juego()
 
    # --------------------------------------------------------------
    # ACTUALIZACIÓN DE LÓGICA
    # --------------------------------------------------------------
    if estado == "INICIO":
        dato_temporizador += dt
        if dato_temporizador > 4.0:
            dato_temporizador = 0.0
            dato_indice = (dato_indice + 1) % len(DATOS_CURIOSOS)
 
    elif estado == "JUEGO":
        tiempo_juego_actual = pygame.time.get_ticks() - tiempo_inicio_juego
        cfg = DIFICULTADES[dificultad_actual]
 
        for ev in chart:
            if not ev["juzgada"] and (tiempo_juego_actual - ev["t"]) > (cfg["bien"] + 40):
                ev["juzgada"] = True
                ev["resultado"] = "Fallo"
                conteo["Fallo"] += 1
                combo = 0
                mostrar_juicio("FALLO", ROJO)
                reproducir(SONIDO_FALLO)
 
        particulas = [p for p in particulas if p.actualizar(dt)]
        for i in range(NUM_CARRILES):
            flash_carril[i] = max(0.0, flash_carril[i] - dt * 3)
        if juicio_timer > 0:
            juicio_timer -= dt
        if combo_pop > 0:
            combo_pop -= dt
 
        notas_pendientes = any(not ev["juzgada"] for ev in chart)
        if tiempo_juego_actual > duracion_cancion_ms + 1200 and not notas_pendientes:
            estado = "FIN"
 
    # --------------------------------------------------------------
    # RENDERIZADO
    # --------------------------------------------------------------
    tiempo_total = pygame.time.get_ticks() / 1000.0
 
    if estado == "INICIO":
        pantalla.blit(FONDO_INICIO, (0, 0))
 
        # bandas de color con notas decorativas flotando (como una previsualización)
        bandas_y = [220, 280, 340]
        bandas_color = [AMARILLO, AZUL, ROJO]
        for i, (by, bc) in enumerate(zip(bandas_y, bandas_color)):
            pygame.draw.rect(pantalla, bc, (0, by, ANCHO, 60))
        for i in range(10):
            x = 40 + i * 78
            y = bandas_y[i % 3] + 30 + math.sin(tiempo_total * 2 + i) * 10
            color = COLORES_CARRIL[i % 4]
            dibujar_nota_icono(pantalla, x, y, color, escala=0.9)
 
        # palmeras decorativas a los lados
        dibujar_palmera(pantalla, 70, 210, tiempo_total, escala=1.1)
        dibujar_palmera(pantalla, 730, 210, tiempo_total + 1.3, escala=1.1)
 
        titulo = render_texto_outline(fuente_titulo, "MacondoBeat", AMARILLO, NEGRO_SUAVE, 4)
        pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 60))
 
        # notita musical decorativa junto al título
        dibujar_nota_icono(pantalla, ANCHO // 2 + titulo.get_width() // 2 - 6, 78, AMARILLO, 1.4)
 
        parpadeo = 180 + int(75 * math.sin(tiempo_total * 4))
        instr = fuente_subtitulo.render("PRESIONA ENTER PARA JUGAR", True, (255, 255, parpadeo))
        pantalla.blit(instr, (ANCHO // 2 - instr.get_width() // 2, 405 - 40))
 
        # dato curioso rotativo
        dato = DATOS_CURIOSOS[dato_indice]
        dato_render = fuente_dato.render(dato, True, (235, 225, 210))
        if dato_render.get_width() > ANCHO - 80:
            dato_render = fuente_dato.render(dato, True, (235, 225, 210))
        pantalla.blit(dato_render, (ANCHO // 2 - dato_render.get_width() // 2, 460))
 
        dif_txt = fuente_dato.render(f"Dificultad: {dificultad_actual}", True, (200, 200, 200))
        pantalla.blit(dif_txt, (ANCHO // 2 - dif_txt.get_width() // 2, 490))
 
        dibujar_boton(pantalla, rect_menu, "MENU")
        dibujar_boton(pantalla, rect_opciones, "OPCIONES")
 
        version = fuente_dato.render("v1.0", True, (150, 150, 150))
        pantalla.blit(version, (ANCHO - version.get_width() - 12, ALTO - 30))
 
        if mostrar_ayuda:
            panel = pygame.Surface((520, 150), pygame.SRCALPHA)
            pygame.draw.rect(panel, (0, 0, 0, 190), panel.get_rect(), border_radius=14)
            pygame.draw.rect(panel, BLANCO, panel.get_rect(), 2, border_radius=14)
            lineas = [
                "Controls: D  F  J  K  to hit the four lanes",
                "Hit each note right when it reaches the glowing line.",
                "Chain hits for combo bonus points!",
                "ESC returns to this menu, ENTER restarts.",
            ]
            for i, linea in enumerate(lineas):
                t = fuente_dato.render(linea, True, BLANCO)
                panel.blit(t, (20, 16 + i * 30))
            pantalla.blit(panel, (ANCHO // 2 - 260, 130))
 
    elif estado == "JUEGO":
        pantalla.blit(FONDO_JUEGO, (0, 0))
        cfg = DIFICULTADES[dificultad_actual]
 
        # carriles
        for i in range(NUM_CARRILES):
            x = CARRILES_X[i]
            base_color = COLORES_CARRIL[i]
            if flash_carril[i] > 0:
                brillo = int(60 * flash_carril[i])
                base_color = tuple(min(255, c + brillo) for c in base_color)
            s = pygame.Surface((CARRIL_ANCHO - 6, ALTO), pygame.SRCALPHA)
            pygame.draw.rect(s, (*base_color, 55), s.get_rect(), border_radius=16)
            pantalla.blit(s, (x + 3, 0))
            pygame.draw.rect(
                pantalla, base_color, (x + 3, HIT_Y - 6, CARRIL_ANCHO - 6, 12), border_radius=6
            )
 
        # línea de golpe (hit line) con resplandor
        glow = pygame.Surface((ANCHO, 30), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 255, 255, 40), glow.get_rect())
        pantalla.blit(glow, (0, HIT_Y - 15))
 
        # etiquetas de teclas
        for i in range(NUM_CARRILES):
            x = CARRILES_X[i] + CARRIL_ANCHO // 2
            escala_tecla = 1.0 + flash_carril[i] * 0.3
            r = int(24 * escala_tecla)
            pygame.draw.circle(pantalla, COLORES_CARRIL_CLARO[i], (x, HIT_Y + 45), r)
            pygame.draw.circle(pantalla, NEGRO_SUAVE, (x, HIT_Y + 45), r, 3)
            letra = fuente_hud.render(CARRIL_LABELS[i], True, NEGRO_SUAVE)
            pantalla.blit(letra, (x - letra.get_width() // 2, HIT_Y + 45 - letra.get_height() // 2))
 
        # notas cayendo
        for ev in chart:
            if ev["juzgada"] and ev["resultado"] != "Fallo":
                continue
            y = HIT_Y - (ev["t"] - tiempo_juego_actual) / 1000.0 * cfg["velocidad"]
            if -30 <= y <= ALTO + 30 and not ev["juzgada"]:
                x = CARRILES_X[ev["carril"]] + CARRIL_ANCHO // 2
                dibujar_nota_icono(pantalla, x, y, COLORES_CARRIL[ev["carril"]])
 
        for p in particulas:
            p.dibujar(pantalla)
 
        # HUD: puntaje y combo
        texto_puntaje = fuente_hud.render(f"Puntaje: {puntaje}", True, BLANCO)
        pantalla.blit(texto_puntaje, (16, 14))
 
        if combo > 1:
            escala_combo = 1.0 + max(0.0, combo_pop) * 1.6
            texto_combo = fuente_grande.render(f"{combo}x", True, AMARILLO)
            texto_combo = pygame.transform.rotozoom(texto_combo, 0, escala_combo)
            pantalla.blit(
                texto_combo, (ANCHO - texto_combo.get_width() - 20, 10)
            )
 
        dif_txt = fuente_dato.render(dificultad_actual, True, (210, 210, 210))
        pantalla.blit(dif_txt, (16, 46))
 
        if juicio_timer > 0:
            alpha = min(255, int(255 * (juicio_timer / 0.5)))
            txt = fuente_juicio.render(juicio_texto, True, juicio_color)
            txt_s = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
            txt_s.blit(txt, (0, 0))
            txt_s.set_alpha(alpha)
            pantalla.blit(txt_s, (ANCHO // 2 - txt.get_width() // 2, HIT_Y - 90))
 
        # barra de progreso de la canción
        progreso = min(1.0, tiempo_juego_actual / duracion_cancion_ms)
        pygame.draw.rect(pantalla, (60, 60, 60), (16, ALTO - 20, ANCHO - 32, 8), border_radius=4)
        pygame.draw.rect(
            pantalla, AMARILLO, (16, ALTO - 20, int((ANCHO - 32) * progreso), 8), border_radius=4
        )
 
    elif estado == "FIN":
        pantalla.blit(FONDO_INICIO, (0, 0))
        dibujar_palmera(pantalla, 90, 200, tiempo_total, escala=1.3)
        dibujar_palmera(pantalla, 710, 200, tiempo_total + 1, escala=1.3)
 
        total_notas = sum(conteo.values())
        precision = 0 if total_notas == 0 else (
            (conteo["Perfecto"] + conteo["Bien"] * 0.5) / total_notas * 100
        )
        if precision >= 90:
            nota_letra, color_letra = "S", AMARILLO
        elif precision >= 75:
            nota_letra, color_letra = "A", (108, 201, 132)
        elif precision >= 55:
            nota_letra, color_letra = "B", (94, 178, 235)
        else:
            nota_letra, color_letra = "C", (235, 111, 105)
 
        titulo = render_texto_outline(fuente_titulo, "Fin de la ronda!", AMARILLO, NEGRO_SUAVE, 3)
        pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 70))
 
        letra_grande = fuente_titulo.render(nota_letra, True, color_letra)
        pantalla.blit(letra_grande, (ANCHO // 2 - letra_grande.get_width() // 2, 160))
 
        lineas = [
            f"Puntaje final: {puntaje}",
            f"Mejor combo: {mejor_combo}x",
            f"Perfecto: {conteo['Perfecto']}    Bien: {conteo['Bien']}    Fallo: {conteo['Fallo']}",
            f"Precision: {precision:.1f}%",
        ]
        for i, linea in enumerate(lineas):
            t = fuente_subtitulo.render(linea, True, BLANCO)
            pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 250 + i * 36))
 
        parpadeo = 180 + int(75 * math.sin(tiempo_total * 4))
        instr = fuente_subtitulo.render(
            "ENTER para jugar de nuevo   |   ESC para el menu", True, (255, 255, parpadeo)
        )
        pantalla.blit(instr, (ANCHO // 2 - instr.get_width() // 2, 430))
 
    pygame.display.flip()
 
pygame.quit()
sys.exit()
