def save_image(base64_data, uploaded_file, folder):
    save_dir = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.png"
    image_path = os.path.join(save_dir, filename)

    if base64_data:
        header, imgstr = base64_data.split(";base64,")
        image_bytes = base64.b64decode(imgstr)
    else:
        image_bytes = uploaded_file.read()

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    return image_path
