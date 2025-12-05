# utils.py

import json
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

from .config import fortune_config, themes_flag_config


def get_copywriting() -> tuple[str, str]:
    """
    Read the copywriting.json, choice a luck with a random content
    """
    _p: Path = fortune_config.fortune_path / "fortune" / "copywriting.json"

    with open(_p, encoding="utf-8") as f:
        content = json.load(f).get("copywriting")
        luck = random.choice(content)
        title: str = luck.get("good-luck")
        text: str = random.choice(luck.get("content"))

        return title, text


def random_basemap(theme: str, spec_path: str | None = None) -> Path:
    """
    随机选择一张底图。
    - 如果指定了 spec_path，直接返回该路径。
    - 如果主题是 'random'，则执行“两阶段随机”：先随机选一个主题，再从该主题中随机选一张图。
    - 如果指定了其他主题，则从该主题文件夹中随机选一张图。
    """
    if isinstance(spec_path, str):
        # 兼容指定签底的功能
        p: Path = fortune_config.fortune_path / "img" / spec_path
        return p

    base_img_path: Path = fortune_config.fortune_path / "img"

    if theme == "random":
        # --- 两阶段随机 ---
        # 第一阶段：随机选择一个主题
        available_themes: list[str] = [
            f.name
            for f in base_img_path.iterdir()
            if f.is_dir() and theme_flag_check(f.name)
        ]

        if not available_themes:
            raise FileNotFoundError("Resource Error: No available themes found!")

        picked_theme_name: str = random.choice(available_themes)
        theme_path: Path = base_img_path / picked_theme_name
    else:
        # 如果是指定主题，直接使用该主题的路径
        theme_path: Path = base_img_path / theme

    # 第二阶段：从选定的主题文件夹中随机选择一张图片
    images_in_theme: list[Path] = [
        f
        for f in theme_path.iterdir()
        if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif")
    ]
    if not images_in_theme:
        raise FileNotFoundError(
            f"Resource Error: No images found for theme '{theme_path.name}'!"
        )

    return random.choice(images_in_theme)


def drawing(gid: str, uid: str, theme: str, spec_path: str | None = None) -> Path:
    # 1. Random choice a base image
    imgPath: Path = random_basemap(theme, spec_path)
    img: Image.Image = Image.open(imgPath).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 2. Random choice a luck text with title
    title, text = get_copywriting()

    # 3. Draw
    font_size = 45
    color = "#F5F5F5"
    image_font_center = [140, 99]
    fontPath = {
        "title": f"{fortune_config.fortune_path}/font/Mamelon.otf",
        "text": f"{fortune_config.fortune_path}/font/sakura.ttf",
    }
    ttfront = ImageFont.truetype(fontPath["title"], font_size)

    # Pillow 10.0.0+ 删除了 getsize，使用 getbbox 替代
    title_bbox = ttfront.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    draw.text(
        (
            image_font_center[0] - title_width / 2,
            image_font_center[1] - title_height / 2,
        ),
        title,
        fill=color,
        font=ttfront,
    )

    # Text rendering
    font_size = 25
    color = "#323232"
    image_font_center = [140, 297]
    ttfront = ImageFont.truetype(fontPath["text"], font_size)
    slices, result = decrement(text)

    for i in range(slices):
        font_height: int = len(result[i]) * (font_size + 4)
        textVertical: str = "\n".join(result[i])
        x: int = int(
            image_font_center[0]
            + (slices - 2) * font_size / 2
            + (slices - 1) * 4
            - i * (font_size + 4)
        )
        y: int = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), textVertical, fill=color, font=ttfront)

    # Save
    outDir: Path = fortune_config.fortune_path / "out"
    if not outDir.exists():
        outDir.mkdir(exist_ok=True, parents=True)

    outPath = outDir / f"{gid}_{uid}.png"

    img.save(outPath)
    return outPath


def decrement(text: str) -> tuple[int, list[str]]:
    """
    Split the text, return the number of columns and text list
    TODO: Now, it ONLY fit with 2 columns of text
    """
    length: int = len(text)
    result: list[str] = []
    cardinality = 9
    if length > 4 * cardinality:
        raise ValueError("Text is too long to fit in the image.")

    col_num: int = 1
    while length > cardinality:
        col_num += 1
        length -= cardinality

    space = " "
    length = len(text)

    if col_num == 2:
        half_len = length // 2
        if length % 2 == 0:
            fillIn = space * (9 - half_len)
            return col_num, [
                text[:half_len] + fillIn,
                fillIn + text[half_len:],
            ]
        else:
            fillIn = space * (9 - (half_len + 1))
            return col_num, [
                text[: half_len + 1] + fillIn,
                fillIn + space + text[half_len + 1 :],
            ]

    for i in range(col_num):
        start = i * cardinality
        end = (i + 1) * cardinality
        result.append(text[start:end])

    return col_num, result


def theme_flag_check(theme: str) -> bool:
    """
    check wether a theme is enabled in themes_flag_config
    """
    return themes_flag_config.model_dump().get(theme + "_flag", False)
