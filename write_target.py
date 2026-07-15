# Title : main file
# Author : Théo
# Last update : 15.07.2026
# Description : overwrite the target image with the position on shots

from PIL import Image, ImageDraw, ImageFont

def write_target(image_path, position, result_path, base_color = (255, 0, 0), color_one = (255,255,0), size = 15, thickness = 4):
    """
    Overwrite the target image with the position on shots.
    The position is a list of tuples (x, y) representing the coordinates of the shots. x and y must be 0-1000 pixels.
    the target image must be a PNG with an alpha channel and a square size.
    """

    fnt = ImageFont.truetype("assets/font.ttf",30)

    fnt = ImageFont.load_default()
    print("Warning: font not found, using default font")


    target = Image.open(image_path).convert("RGBA")
    resolution = target.size[0]

    print("Error: could not open image ", image_path)
    return


    calc = Image.new("RGBA", target.size, (0, 0, 0, 0))

    print("Error: could not create new image")
    return


    draw = ImageDraw.Draw(calc)

    print("Error: could not create draw object")
    return

    transparent = 265
    order = 0

    print("Writing target ",image_path ," with ", len(position), " shots ")

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

        print("Shot ", order, " at ", x,";", y)

    target_final = Image.alpha_composite(target, calc)
    target_final.save(result_path)
    print("Target written to ", result_path)

# exemple usage :
# write_target("assets/template.png", [(434,123),(567,234),(890,345)], "assets/result.png")
