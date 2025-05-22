from machine import UART, Pin, SPI
from ili9341 import Display, color565
from xglcd_font import XglcdFont
import time

# === Définition des couleurs ===
COULEUR_NOIR = color565(0, 0, 0)
COULEUR_BLANC = color565(255, 255, 255)
COULEUR_VERT = color565(0, 255, 0)
COULEUR_BLEU = color565(0, 150, 255)
COULEUR_CYAN = color565(180, 220, 255)

rs485_uart = UART(1, baudrate=4800, tx=27, rx=26)
rs485_commande = Pin(25, Pin.OUT)
rs485_commande.value(0)  # On commence en réception

trame_direction_vent = b'\x01\x03\x00\x00\x00\x01\x84\x0A'  
trame_vitesse_vent = b'\x02\x03\x00\x00\x00\x01\x84\x39'    

libelles_directions = {
    0: "Nord", 1: "Nord-Est", 2: "Est", 3: "Sud-Est",
    4: "Sud", 5: "Sud-Ouest", 6: "Ouest", 7: "Nord-Ouest"
}

def traduire_direction(code):
    return libelles_directions.get(code, "Inconnue")

# === Communication avec les capteurs ===
def envoyer_trame(trame):
    rs485_commande.value(1)        # Activer la transmission
    time.sleep(0.01)
    rs485_uart.write(trame)
    time.sleep(0.01)
    rs485_commande.value(0)        # Repasser en réception
    time.sleep(0.05)

def lire_donnee_capteur(trame, id_attendu):
    envoyer_trame(trame)
    time.sleep(0.1)
    reponse = rs485_uart.read()
    if reponse and reponse[0] == id_attendu and len(reponse) >= 5:
        return (reponse[3] << 8) | reponse[4]
    return None

def obtenir_direction_vent():
    valeur = lire_donnee_capteur(trame_direction_vent, 1)
    return traduire_direction(valeur) if valeur is not None else "Erreur"

def obtenir_vitesse_vent():
    valeur = lire_donnee_capteur(trame_vitesse_vent, 2)
    return round(valeur * 0.1, 2) if valeur is not None else 0.0

# === Configuration de l'écran ILI9341 ===
spi_ecran = SPI(1, baudrate=60_000_000, sck=Pin(14), mosi=Pin(13))
ecran = Display(spi_ecran, dc=Pin(2), cs=Pin(15), rst=Pin(4), width=320, height=240, rotation=90)
Pin(21, Pin.OUT).on()  # rétroéclairage
police_texte = XglcdFont('fonts/Unispace12x24.c', 12, 24)

# === Heure actuelle (format HH:MM) ===
def heure_locale():
    t = time.localtime()
    return f"{t[3]:02}:{t[4]:02}"

# === Affichage de texte à l'écran ===
def afficher_texte(x, y, message, couleur=COULEUR_BLANC, fond=COULEUR_NOIR):
    ecran.draw_text(x, y, message, police_texte, couleur, fond)

# === Page 1 : affichage d'une image ===
def afficher_image_logo():
    ecran.clear(COULEUR_BLANC)
    ecran.draw_image("projet.raw", 40, 0, 240, 240)

# === Page 2 : affichage des données météo ===
def afficher_donnees_meteo():
    ecran.clear(COULEUR_NOIR)
    afficher_texte(40, 20, "CAPITAINERIE DATA", COULEUR_BLEU)

    afficher_texte(24, 70, "Vitesse du vent :", COULEUR_BLANC)
    afficher_texte(24, 100, f"{obtenir_vitesse_vent()} m/s", COULEUR_VERT)

    afficher_texte(24, 140, "Direction du vent :", COULEUR_BLANC)
    afficher_texte(24, 170, obtenir_direction_vent(), COULEUR_VERT)

    heure = heure_locale()
    x = ecran.width - (len(heure) * police_texte.width) - 10
    y = ecran.height - police_texte.height - 5
    afficher_texte(x, y, heure, COULEUR_CYAN)

# === Diaporama automatique ===
diapos = [afficher_image_logo, afficher_donnees_meteo]

try:
    while True:
        for page in diapos:
            page()
            time.sleep(5)
except KeyboardInterrupt:
    print("Programme arrêté")
    ecran.cleanup()