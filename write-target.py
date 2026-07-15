# Title : main file
# Author : Théo
# Last update : 15.07.2026
# Description : overwrite the target image with the position on shots

from PIL import Image, ImageDraw, ImageFont
from test import pos

def write_target(image_path, position, result_path, base_color = (255, 0, 0), color_one = (255,255,0), size = 15, thickness = 5):
    """
    Overwrite the target image with the position on shots.
    The position is a list of tuples (x, y) representing the coordinates of the shots. x and y must be 0-1000 pixels.
    the target image must be a PNG with an alpha channel and a square size.
    """
    fnt = ImageFont.truetype("assets/font.ttf",30)

    target = Image.open(image_path).convert("RGBA")
    resolution = target.size[0]

    calc = Image.new("RGBA", target.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(calc)

    transparent = 265
    order = 0

    for coord in position :
        x = coord[0]  * resolution / 1000
        y = coord[1] * resolution / 1000

        transparent -= 16
        if transparent < 0:
            transparent = 10

        if transparent == 255:
            color = color_one
        else:
            color = base_color

        color = color + (transparent,)

        order += 1


        draw.line((x - size, y, x + size, y), fill=color, width=thickness)
        draw.line((x, y - size, x, y + size), fill=color, width=thickness)
        draw.text((x +size, y + size),str(order), fill=color, font=fnt)

    target_final = Image.alpha_composite(target, calc)
    target_final.save(result_path)


write_target("assets/template.png", [(0,0),(1000,1000),(500,500)], "assets/result.png")
