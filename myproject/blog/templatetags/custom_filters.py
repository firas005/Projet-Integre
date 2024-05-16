from django import template

register = template.Library()

@register.filter(name='is_image')

def is_image(filename):
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
    return any(filename.lower().endswith(ext) for ext in image_extensions)

@register.filter(name='file_icon')
def file_icon(extension):
    """
    Custom template filter to map file extensions to icon URLs.
    """
    if extension == ".pdf":
        return "/static/images/pdf_icon.png"
    elif extension in ['.doc', '.docx']:
        return "/static/images/word_icon.png"
    elif extension in ['.xls', '.xlsx']:
        return "/static/images/excel_icon.png"
    elif extension in ['.mp3', '.wav', '.ogg']:
        return "/static/images/audio_icon.png"
    elif extension in ['.mp4', '.avi', '.mov']:
        return "/static/images/video_icon.png"
    else:
        return "/static/images/generic_file_icon.png"