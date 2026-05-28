import pygame

pygame.init()

ANCHO = 800
ALTO  = 600

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("MacondoBeat")
reloj = pygame.time.Clock()

corriendo = True
while corriendo:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            corriendo = False

    pantalla.fill((20, 10, 5))
    pygame.display.flip()
    reloj.tick(60)

pygame.quit() # APARECER PANTALLA NEGRA CON EL TITULO "MACONDO BEAT" Y SE CIERRA CUANDO SE HACE CLICK EN LA X DE LA VENTANA




import pygame

pygame.init()

ANCHO = 800
ALTO = 600
FONDO = (20, 10, 5)

COLORES = [
    (240, 192, 96),
    (100, 200, 100),
    (80, 180, 220),
    (220, 120, 80),
]

CARRILES_X = [250, 330, 410, 490]
CARRIL_ANCHO = 80

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("MacondoBeat")
reloj = pygame.time.Clock()

corriendo = True
while corriendo:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            corriendo = False

    pantalla.fill(FONDO)

    for i in range(4):
        pygame.draw.rect(
            pantalla,
            COLORES[i],
            (CARRILES_X[i], 0, CARRIL_ANCHO, ALTO),
            2
        )

    pygame.display.flip()
    reloj.tick(60)

pygame.quit()
