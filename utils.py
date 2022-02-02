from constants import DIMS


def intersects(min_coords1, max_coords1, min_coords2, max_coords2):
    for i in range(DIMS):
        if max_coords1[i] <= min_coords2[i] or max_coords2[i] <= min_coords1[i]:
            return False

    return True
