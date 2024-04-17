from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import io

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    blocked_users = models.ManyToManyField(User, related_name='blocked_by', blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    #def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the model instance first

        # Open the image using its path stored in self.image.path
        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)

            # Instead of saving the path, use the in-memory image object
            # and a temporary file-like object for Django's FieldFile.save()
            temp_file = io.BytesIO()
            img.save(temp_file, format=img.format)  # Save the resized image to the temporary file
            temp_file.seek(0)  # Reset the cursor to the beginning of the file

            # Now you can use temp_file as the content for FieldFile.save()
            self.image.save(self.image.name, temp_file)  # Save the resized image to the same filename


    
        
#@property
#def fullname(self):
#    return f"{self.user.first_name} {self.user.last_name}"

# Create your models here.

# Create your models here.
