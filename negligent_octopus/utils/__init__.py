def get_filename_extension(filename: str):
    return filename.rsplit(".", 1)[1]


def get_filename_no_extension(filename: str):
    try:
        return filename.rsplit(".", 1)[0]
    except IndexError:
        return filename
