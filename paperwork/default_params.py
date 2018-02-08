from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch

PAPER_SIZE = landscape(letter)
BATCH = 20
TIME_ZONE = 'America/New_York'
MARGIN = 0.25 * inch, 0.25 * inch

ANCHOR_SIZE = 0.4 * inch

BAR_WIDTH = 0.02 * inch
BAR_HEIGHT = 0.4 * inch

SCALE_W = 1.5 * inch

MIN_COLOR = 0.5

MAX_SCALE = 1.0

PPI = 100

IMAGE_MARGIN = 0.05 * inch
