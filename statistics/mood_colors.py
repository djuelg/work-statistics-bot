def get_mood_color(mood):
    # Return existing color if mood is in the dictionary
    if mood in MOOD_COLORS_DICT:
        return MOOD_COLORS_DICT[mood]

    # If not, deterministically select a color from the list
    index = hash(mood) % len(MOOD_COLORS_DICT.values())
    return list(MOOD_COLORS_DICT.values())[index]


MOOD_COLORS_DICT = {
    'glücklich': (152, 251, 152),       # palegreen
    'krank': (240, 128, 128),           # coral
    'ausgeglichen': (245, 222, 179),    # wheat
    'ruhig': (135, 206, 235),           # skyblue
    'genervt': (255, 165, 0),           # orange
    'produktiv': (240, 128, 128),       # lightcoral
    'unruhig': (240, 230, 140),         # khaki
    'zufrieden': (32, 178, 170),        # lightseagreen
    'ängstlich': (176, 196, 222),       # lightsteelblue
    'traurig': (173, 216, 230),         # lightblue
    'motiviert': (238, 232, 170),       # palegoldenrod
    'dankbar': (255, 182, 193),         # lightpink
    'stolz': (255, 218, 185),           # peachpuff
    'unsicher': (255, 240, 245),        # lavenderblush
    'wütend': (250, 128, 114),          # salmon
    'hoffnungsvoll': (255, 255, 224),   # lightyellow
    'erschöpft': (211, 211, 211),       # lightgray
    'neugierig': (224, 255, 255),       # lightcyan
    'verliebt': (221, 160, 221),        # plum
    'einsam': (176, 224, 230),          # powderblue
    'melancholisch': (216, 191, 216),   # thistle
    'erleichtert': (245, 255, 250),     # mintcream
    'eifersüchtig': (219, 112, 147),    # palevioletred
    'optimistisch': (250, 250, 210),    # lightgoldenrodyellow
    'frustriert': (255, 160, 122),      # lightsalmon
    'bedrückt': (176, 196, 222),        # lightsteelblue
    'überfordert': (240, 128, 128),     # lightcoral
    'gelassen': (144, 238, 144),        # lightgreen
    'überrascht': (230, 230, 250),      # lavender
    'enttäuscht': (188, 143, 143),      # rosybrown
    'leidenschaftlich': (255, 182, 193),# lightpink
    'erschrocken': (250, 250, 210)      # lightgoldenrod
}
