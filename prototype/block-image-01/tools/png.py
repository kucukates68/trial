import zlib, struct
def write_png(path, w, h, rgb):  # rgb: list of (r,g,b) row-major
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w): raw.extend(rgb[y * w + x])
    def chunk(t, d): c = struct.pack('>I', len(d)) + t + d; return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(raw))) + chunk(b'IEND', b''))
def hexrgb(h): return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
