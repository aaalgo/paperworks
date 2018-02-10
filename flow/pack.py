
# test with or without rotate
#      cut along x or y
# return optimal filling method
# score == 0 means not feaisble
def divide (w0, h0, W, H):
    best = 0
    best_rotate = None
    best_along_x = None
    for rotate in [False, True]:
        if rotate:
            w, h = h0, w0
        else:
            w, h = w0, h0
        if w < W and h < H:
            # along X
            v = max(min(W-w, h), min(W, H-h))
            if v > best:
                best = v
                best_rotate = rotate
                best_along_x = True
            v = max(min(W-w, H), min(w, H-h))
            if v > best:
                best = v
                best_rotate = rotate
                best_along_x = False
                pass
            pass
        pass
    return best, best_rotate, best_along_x

def pack (layout, images):     # item: (id, w, h)
    # return pages
    #        page: [items]
    #        item: id, x, y, rotated
    x0, y0, x1, y1 = layout.imagebb
    width, height = x1 - x0, y1 - y0
    pages = []
    bins = []   # [page, x, y, w, h]
    # reverse sort by size
    for uid, w, h in sorted(images, key=lambda im: -im[1] * im[2]):
        assert w <= width
        assert h <= height
        # try to find a bin that fits image
        best = None
        best_score = None
        best_rotate = None
        best_along_x = None     # cut along x
        for i, (_, _, _, W, H) in enumerate(bins):
            score, rotate, along_x = divide(w, h, W, H)
            if score == 0:
                continue
            if best is None or score > best_score:
                best = i
                best_score = score
                best_rotate = rotate
                best_along_x = along_x
            pass
        if best is None:
            best = len(bins)
            bins.append([len(pages), 0, 0, width, height])
            pages.append([])
            best_score, best_rotate, best_along_x = divide(w, h, width, height)
            pass
        # split
        page, x, y, W, H = bins[best]

        if best_rotate:
            w, h = h, w
            pass
        # do not rotate
        pages[page].append([uid, x, y, best_rotate])
        if best_along_x:
            bins.append([page, x+w, y, W-w, h])
            bins[best] = [page, x, y+h, W, H-h]
        else:
            bins.append([page, x, y + h, w, H-h])
            bins[best] = [page, x+w, y, W-w, H]
        pass
    return pages
