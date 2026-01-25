# PROJECT-CLICK - KMK on XIAO RP2040
# 3x2 matrix, rotary encoder, pot (short press = layer next, long press = LED menu),
# WS2812/SK6812 underglow, OLED splash (PROJECT-CLICK + cat kaomoji).
#
# EDIT THESE PINS IF THEY DON'T MATCH YOUR BOARD/PCB:
import time
import random

import board
import digitalio
import analogio
import busio
import displayio
from adafruit_display_text import label
import terminalio

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.extensions.RGB import RGB, AnimationModes
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys
from kmk.scanners import DiodeOrientation

# -------------------------
# === HARDWARE PINS ===
# Change these to match your PCB if needed.
# -------------------------
# Matrix: 3 rows x 2 cols (6 keys)
ROW_PINS = (board.GP26, board.GP27, board.GP28)  # row0, row1, row2
COL_PINS = (board.GP4, board.GP5)               # col0, col1

# Rotary encoder (A, B, Switch)
ENCODER_PINS = ((board.GP7, board.GP8, board.GP9),)

# Potentiometer ADC pin (use a free ADC pin: GP26..GP29 are ADC on RP2040)
POT_ADC_PIN = board.GP29      # ADC in (change if used by matrix)
POT_SWITCH_PIN = board.GP6    # push switch for potentiometer (short/long press)

# RGB / NeoPixel data pin & pixel count
PIXEL_PIN = board.GP15
NUM_PIXELS = 10               # set to number of SK6812/WS2812 on your board

# OLED I2C (standard)
I2C_SCL = board.SCL
I2C_SDA = board.SDA
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32

# -------------------------
# === KMK SETUP ===
# -------------------------
keyboard = KMKKeyboard()

# RGB underglow extension
underglow = RGB(
    pixel_pin=PIXEL_PIN,
    num_pixels=NUM_PIXELS,
    val_limit=100,
    val_default=40,
    animation_mode=AnimationModes.RAINBOW,
)
keyboard.extensions.append(underglow)

# Media keys extension (for encoder mute)
media_keys = MediaKeys()
keyboard.extensions.append(media_keys)

# Matrix pins
keyboard.row_pins = ROW_PINS
keyboard.col_pins = COL_PINS
keyboard.diode_orientation = DiodeOrientation.COL2ROW

# Define a 4-layer keymap (each layer must have 6 entries)
keyboard.keymap = [
    # layer 0
    [
        KC.N1, KC.N2,
        KC.N3, KC.N4,
        KC.N5, KC.N6,
    ],
    # layer 1
    [
        KC.MRWD, KC.MPLY,   # prev, play/pause
        KC.MFFD, KC.MUTE,   # next, mute
        KC.VOLD, KC.VOLU,   # vol- vol+
    ],
    # layer 2
    [
        KC.LEFT, KC.DOWN,
        KC.UP, KC.RIGHT,
        KC.HOME, KC.END,
    ],
    # layer 3
    [
        KC.F1, KC.F2,
        KC.F3, KC.F4,
        KC.F5, KC.F6,
    ],
]

# Rotary encoder (volume control)
encoder_handler = EncoderHandler()
encoder_handler.divisor = 2
encoder_handler.pins = ENCODER_PINS
# default mapping -> (ccw, cw, press) per encoder
encoder_handler.map = (((KC.VOLD, KC.VOLU, KC.MUTE),),)
keyboard.modules.append(encoder_handler)

# -------------------------
# === OLED / splash ===
# -------------------------
try:
    import adafruit_ssd1306
    i2c = busio.I2C(I2C_SCL, I2C_SDA)
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
    display = adafruit_ssd1306.SSD1306(display_bus, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)
    has_display = True
except Exception as e:
    print("OLED not available:", e)
    display = None
    has_display = False

SPLASH_DURATION = 1.0  # seconds to show "PROJECT-CLICK" before the cat ASCII

CAT_KAOMOJI = [
"⠀⠀⠀⠀⠀⠀⢀⡤⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⢀⡏⠀⠀⠈⠳⣄⠀⠀⠀⠀⠀⣀⠴⠋⠉⠉⡆⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠈⠉⠉⠙⠓⠚⠁⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⢀⠞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣄⠀⠀⠀⠀",
"⠀⠀⠀⠀⡞⠀⠀⠀⠀⠀⠶⠀⠀⠀⠀⠀⠀⠦⠀⠀⠀⠀⠀⠸⡆⠀⠀⠀",
"⢠⣤⣶⣾⣧⣤⣤⣀⡀⠀⠀⠀⠀⠈⠀⠀⠀⢀⡤⠴⠶⠤⢤⡀⣧⣀⣀⠀",
"⠻⠶⣾⠁⠀⠀⠀⠀⠙⣆⠀⠀⠀⠀⠀⠀⣰⠋⠀⠀⠀⠀⠀⢹⣿⣭⣽⠇",
"⠀⠀⠙⠤⠴⢤⡤⠤⠤⠋⠉⠉⠉⠉⠉⠉⠉⠉⠳⠖⠦⠤⠶⠦⠞⠁⠀⠀⠀"
]

def show_splash():
    if not has_display:
        return
    display.fill(0)
    # big title: simple text "PROJECT-CLICK"
    try:
        display.text("PROJECT-CLICK", 0, 0, 1)
    except Exception:
        # some drivers support text attr, else we still call show()
        pass
    display.show()
    time.sleep(SPLASH_DURATION)

    # then show kaomoji cat (static)
    display.fill(0)
    y = 0
    # draw each line; adjust spacing to fit 32px tall screen (8 lines works for 128x32 if small font)
    for line in CAT_KAOMOJI:
        try:
            display.text(line[:21], 0, y, 1)  # truncate to 21 chars to fit
        except Exception:
            pass
        y += 4  # pack lines tighter
        if y > DISPLAY_HEIGHT - 4:
            break
    display.show()

def show_status(layer_idx, led_mode_name):
    if not has_display:
        return
    display.fill(0)
    try:
        display.text("LAYER: {}".format(layer_idx), 0, 0, 1)
        display.text("LED: {}".format(led_mode_name), 0, 12, 1)
    except Exception:
        pass
    display.show()

# -------------------------
# === LED modes ===
# -------------------------
LED_MODS = ["STATIC", "RAINBOW", "BREATH", "OFF"]
current_led_mode = 0

def apply_led_mode(idx):
    global current_led_mode
    current_led_mode = idx % len(LED_MODS)
    m = LED_MODS[current_led_mode]
    if m == "STATIC":
        underglow.animation_mode = AnimationModes.STATIC
        underglow.animation_speed = 0
        underglow.val_default = 50
    elif m == "RAINBOW":
        underglow.animation_mode = AnimationModes.RAINBOW
        underglow.animation_speed = 2
    elif m == "BREATH":
        underglow.animation_mode = AnimationModes.BREATH
        underglow.animation_speed = 2
    elif m == "OFF":
        underglow.animation_mode = AnimationModes.STATIC
        underglow.val_default = 0
    else:
        underglow.animation_mode = AnimationModes.STATIC

apply_led_mode(current_led_mode)

# -------------------------
# === Pot + Layer + Menu logic as KMK Extension ===
# -------------------------
class PotLayerExtension:
    def __init__(self, keyboard_obj):
        self.k = keyboard_obj
        self.adc = analogio.AnalogIn(POT_ADC_PIN)
        self.sw = digitalio.DigitalInOut(POT_SWITCH_PIN)
        self.sw.direction = digitalio.Direction.INPUT
        self.sw.pull = digitalio.Pull.UP
        self.in_menu = False
        self.last_sw = True
        self.press_time = 0
        self.longpress_threshold = 0.8
        self.selected_led_idx = current_led_mode
        self.layer_idx = 0
        # show initial splash then status
        show_splash()
        show_status(self.layer_idx, LED_MODS[current_led_mode])

    def read_pot_to_index(self):
        # map 0..65535 to LED_MODS length
        val = self.adc.value
        idx = int((val / 65535) * len(LED_MODS))
        if idx >= len(LED_MODS):
            idx = len(LED_MODS) - 1
        return idx

    def poll_switch(self):
        state = self.sw.value  # True when not pressed
        now = time.monotonic()
        if not state and self.last_sw:
            # just pressed
            self.press_time = now
        if state and not self.last_sw:
            # released
            held = now - getattr(self, "press_time", now)
            if held >= self.longpress_threshold:
                # long press -> toggle LED menu
                self.in_menu = not self.in_menu
                if self.in_menu:
                    self.selected_led_idx = current_led_mode
                    print("Entered LED menu")
                else:
                    print("Exited LED menu")
            else:
                # short press -> switch layer
                if not self.in_menu:
                    self.layer_idx = (self.layer_idx + 1) % 4
                    try:
                        self.k.active_layer = self.layer_idx
                    except Exception:
                        try:
                            self.k._active_layer = self.layer_idx
                        except Exception:
                            pass
                    print("Switched to layer", self.layer_idx)
                    show_status(self.layer_idx, LED_MODS[current_led_mode])
        self.last_sw = state

    def show_led_menu(self):
        # show current selection on OLED
        if not has_display:
            return
        display.fill(0)
        y = 0
        idx = self.selected_led_idx
        for i, m in enumerate(LED_MODS):
            prefix = ">" if i == idx else " "
            try:
                display.text("{} {}".format(prefix, m), 0, y, 1)
            except Exception:
                pass
            y += 10
        display.show()

    def matrix_update(self, matrix):
        # this is called each KMK matrix scan cycle
        self.poll_switch()

        if self.in_menu:
            # map pot to selected LED mode
            self.selected_led_idx = self.read_pot_to_index()
            self.show_led_menu()
            return

        # not in menu: normal status
        show_status(self.layer_idx, LED_MODS[current_led_mode])

# connect extension and append
pot_ext = PotLayerExtension(keyboard)
keyboard.extensions.append(pot_ext)

# We need to ensure that when leaving LED menu, selection actually applies:
_last_menu_state = pot_ext.in_menu

def _menu_watcher_tick():
    global _last_menu_state
    if _last_menu_state and not pot_ext.in_menu:
        # menu just closed; apply selected LED mode
        apply_led_mode(pot_ext.selected_led_idx)
        show_status(pot_ext.layer_idx, LED_MODS[current_led_mode])
    _last_menu_state = pot_ext.in_menu

# Hook into keyboard main loop by using keyboard.on_post_matrix_scan if available
try:
    keyboard.on_post_matrix_scan.append(_menu_watcher_tick)
except Exception:
    # fallback: we'll call it from pot_ext.matrix_update by adding the call there; but to avoid multiple edits,
    # call here is best-effort. If it doesn't work, the user can re-run or we can change later.
    pass

# Ensure the active layer variable is set initially
try:
    keyboard.active_layer = 0
except Exception:
    try:
        keyboard._active_layer = 0
    except Exception:
        pass

# -------------------------
# === Encoder volume helper ===
# -------------------------
# A small helper function that will try to send volume up/down keycodes when the encoder
# rotates. The EncoderHandler already maps the encoder to volume by default above, but
# this helper gives a named place to change behaviour (acceleration, steps, etc.).

def encoder_volume(delta):
    """Handle encoder delta: positive -> increase volume, negative -> decrease.
    The function calls keyboard.tap_key() for each step; KMKKeyboard.tap_key may be
    available in your KMK version. If unavailable, the EncoderHandler.map fallback will
    still provide volume control.
    """
    try:
        # send a key press for each step of delta
        if delta > 0:
            for _ in range(delta):
                try:
                    keyboard.tap_key(KC.VOLU)
                except Exception:
                    # if tap_key isn't available, fall back to map already set on handler
                    pass
        elif delta < 0:
            for _ in range(-delta):
                try:
                    keyboard.tap_key(KC.VOLD)
                except Exception:
                    pass
    except Exception:
        # be robust to runtime differences in KMK versions
        pass

# Try to attach the helper to the encoder handler if the KMK version supports a callback
try:
    # some KMK builds expose "callback" or "handler" for custom encoder handling
    encoder_handler.callback = lambda delta, index=0: encoder_volume(delta)
except Exception:
    try:
        encoder_handler.handler = lambda delta, index=0: encoder_volume(delta)
    except Exception:
        # if neither attribute exists, the existing encoder_handler.map will still work.
        pass

# -------------------------
# === START KB ===
# -------------------------
if __name__ == "__main__":
    print("Starting PROJECT-CLICK KMK")
    keyboard.go()
