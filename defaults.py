from reportlab.lib.pagesizes import letter, A4, landscape
from layout import LetterSizeLandscapeLayout

TIME_ZONE = 'America/New_York'

LAYOUT = LetterSizeLandscapeLayout()
BATCH = 20

MIN_COLOR = 128 # [0, 1]

ALLOW_REVERSE_COLOR = True
ALLOW_ROTATE = True

IMAGE_PPI = 100
SCAN_PPI = 200

HUE_TH = 10
SATURATE_TH = 0.1
BLACK_TH = 50

SAMPLE_TH = 1000

CLASS_GAP = 20
CLASS_RELAX = 2

SMALL_OBJECT = 5

BRIGHTEN = 20

