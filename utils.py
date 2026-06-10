# Farbe eines Streckenabschnitts bestimmen
def get_color(temp, humidity):
    if temp >= 25 and humidity >= 80:
        return "red"
    elif temp >= 25:
        return "orange"
    elif humidity >= 80:
        return "yellow"
    else:
        return "blue"

# Teilt GPS-Punkte in farbige Streckenabschnitte auf.
def build_segments(rows, get_color):
    segments = []
    current_color = None
    current_coords = []

    for row in rows:
        temp = float(row[3])
        humidity = float(row[4])
        color = get_color(temp, humidity)
        coord = (float(row[1]), float(row[2]))

        if color != current_color:
            if current_coords:
                segments.append((current_color, current_coords))
                
                # letzte Punkt wird als Startpunkt des neuen Abschnitts übernommen.
                current_coords = [current_coords[-1]]
            current_color = color

        current_coords.append(coord)

    if current_coords:
        segments.append((current_color, current_coords))

    return segments