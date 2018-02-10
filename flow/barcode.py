import subprocess

def barcode_encode (batch_page):
    return '%d %d.' % (batch_page.batch.id, batch_page.page.id)

def barcode_decode (symbol):
    x, y = symbol.split(' ')
    return int(x), int(y[0])

def barcode_scan (path):
    symbol = subprocess.check_output("zbarimg %s" % path, shell=True)
    symbol = symbol.strip()
    if symbol is None or len(symbol) == 0:
        print("ERROR, %s not recognized")
        return
    symbol = symbol.decode('ascii')
    assert len(symbol) > 0
    symbol = symbol.split(':')[1].split('.')[0]
    return barcode_decode(symbol)
