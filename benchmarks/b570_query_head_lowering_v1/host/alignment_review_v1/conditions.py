"""Integer byte arithmetic from the frozen source; not a hardware simulator."""
def descriptor(offset, alignment, element):
    if alignment <= 0 or alignment & (alignment - 1) or element <= 0:
        raise ValueError('positive power-of-two descriptor alignment and element size required')
    base = offset & ~(alignment - 1)
    while (offset - base) % element:
        if base < alignment:
            raise ValueError('frozen descriptor backtracking would assert')
        base -= alignment
    return base, offset-base


def span(ne, nb, element):
    return element + sum((n-1)*stride for n,stride in zip(ne, nb))


def aligned_mask_slab(source, n, j):
    # One extra CPU materialization per PQ query; no row padding or stride change.
    return source[j*n*4:(j+1)*n*4]


def logical_q_addresses(q, h, prefix):
    return [prefix+4*((j*h+head)*128+d) for j in range(q) for head in range(h) for d in range(128)]
