from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from projectapp.models import Project
from django.core.files.base import ContentFile
import cv2
import io
from PIL import Image, ImageOps, ImageFile 
from django.core.files.storage import default_storage
import numpy as np
from io import BytesIO, StringIO
from multiselectfield import MultiSelectField
import os 
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
import sys
import torch 
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
from network.Transformer import Transformer
import uuid
from rembg.bg import remove


ACTION_CHOICES = (
        ("NO_FILTER", "원본 사진"),
        ("HAYAO", "HAYAO 화풍"),
        ("HOSODA", "HOSODA 화풍"),
        ("SHINKAI", "SHINKAI 화풍"),
        ("PAPRIKA", "PAPRIKA 화풍"), 
    )


class Article(models.Model): 
    writer = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='article', null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name='article', null=True)
    title = models.CharField(max_length=200, null =True)
    image = models.ImageField(upload_to='article/', null=True, blank=True)
    image_converted = models.ImageField(upload_to='article/converted/', null=True, blank=True)
    style = models.CharField(max_length = 50, blank = True, null=True, choices=ACTION_CHOICES)
    content = models.TextField(null=True)
    created_at = models.DateField(auto_now_add=True, null=True)
    like = models.IntegerField(default=0)


    def convert_image(self, *args, **kwargs):
        image_converted = convert_rbk(self.image, self.style)
        
        self.image_converted = InMemoryUploadedFile(file=image_converted, 
                                                    field_name="ImageField",

                                                    name=self.image.name, 
                                                    content_type='image/png', 
                                                    size=sys.getsizeof(image_converted), 
                                                    charset=None)
                                



def convert_rbk(img, style):
    if style == "HAYAO":
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        default_storage.save("test/"+"0.png", img)

        initial_image = "./media/test/0.png"
        result_image1 = ""
        result_image2 = settings.MEDIA_ROOT +"/test/2.png"

        f = np.fromfile(initial_image)
        result = remove(f)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(result_image2)

        model = Transformer()
        model.load_state_dict(torch.load('pretrained_model/Hayao_net_G_float.pth'))
        model.eval()

        img_size = 450
        img = cv2.imread(initial_image)

        T = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(img_size, 2),
            transforms.ToTensor()
        ])

        img_input = T(img).unsqueeze(0)

        img_input = -1 + 2 * img_input

        img_output = model(img_input)

        img_output = (img_output.squeeze().detach().numpy() + 1.) /2.
        img_output = img_output.transpose([1,2,0])
        img_output = cv2.convertScaleAbs(img_output, alpha = (255.0)) 
        cv2.imwrite(result_image1, img_output) 

        #0.png: Original image, 1.png: converted image 2.png: background removed image
        src1 = cv2.imread(result_image2, cv2.IMREAD_UNCHANGED)  #background removed
        src = cv2.imread(result_image1, cv2.IMREAD_COLOR)        #converted image
        h, w = img.shape[:2]    # shape of original image
        h1, w1 = src1.shape[:2]     #shage or background removed image

        if [h,w] != [h1, w1]:
            src1 = cv2.rotate(src1, cv2.ROTATE_90_CLOCKWISE)

        src = cv2.resize(src, dsize=(w, h), interpolation=cv2.INTER_AREA) #원본사진이랑 그림으로 바꾼 사진 크기 맞추기 
        for y in range (h):
            for x in range(w):
                img[y,x] = 255

        mask = src1[:, :, -1] #(1440, 666)
        th, mask1 = cv2.threshold(mask, 2, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        mask1 = cv2.resize(mask1, dsize=(w,h), interpolation=cv2.INTER_AREA )

        i = settings.MEDIA_ROOT +"/test/3.png" #mask
        cv2.imwrite(i, mask1)


        j = settings.MEDIA_ROOT +"/test/4.png" #copy mask pixel
        cv2.copyTo(src, mask1, img)
        cv2.imwrite(j, img)

        k = settings.MEDIA_ROOT +"/test/5.png"
        f1 = np.fromfile(j)
        result = remove(f1)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(k)

        img = Image.open(k)
        os.remove(i)  
        os.remove(j)
        os.remove(k)
        os.remove(initial_image)
        os.remove(result_image1)
        os.remove(result_image2)
        return image_to_bytes(img)
    
    if style == "HOSODA":
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        default_storage.save("test/"+"0.png", img)

        initial_image = "./media/test/0.png"
        result_image1 = "./media/test/1.png"
        result_image2 = settings.MEDIA_ROOT +"/test/2.png"

        f = np.fromfile(initial_image)
        result = remove(f)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(result_image2)

        model = Transformer()
        model.load_state_dict(torch.load('pretrained_model/Hosoda_net_G_float.pth'))
        model.eval()

        img_size = 450
        img = cv2.imread(initial_image)


        T = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(img_size, 2),
            transforms.ToTensor()
        ])

        img_input = T(img).unsqueeze(0)

        img_input = -1 + 2 * img_input

        img_output = model(img_input)

        img_output = (img_output.squeeze().detach().numpy() + 1.) /2.
        img_output = img_output.transpose([1,2,0])
        img_output = cv2.convertScaleAbs(img_output, alpha = (255.0)) 
        cv2.imwrite(result_image1, img_output) 

        #0.png: 원본 사진, 1.png: 그림으로 바뀐 사진 2.png: 배경을 없앤 사진 
        src1 = cv2.imread(result_image2, cv2.IMREAD_UNCHANGED)  #배경 없앤 사진 
        src = cv2.imread(result_image1, cv2.IMREAD_COLOR)        #그림으로 바꾼 사진 
        h, w = img.shape[:2]    #원본 사진의 shape
        h1, w1 = src1.shape[:2]     #배경 없앤 사진의 shape

        if [h,w] != [h1, w1]:
            src1 = cv2.rotate(src1, cv2.ROTATE_90_CLOCKWISE)

        src = cv2.resize(src, dsize=(w, h), interpolation=cv2.INTER_AREA) #원본사진이랑 그림으로 바꾼 사진 크기 맞추기 
        for y in range (h):
            for x in range(w):
                img[y,x] = 255


        mask = src1[:, :, -1] #(1440, 666)
        th, mask1 = cv2.threshold(mask, 2, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        mask1 = cv2.resize(mask1, dsize=(w,h), interpolation=cv2.INTER_AREA )

        i = settings.MEDIA_ROOT+"/test/3.png" #마스크
        cv2.imwrite(i, mask1)

        j = settings.MEDIA_ROOT+"/test/4.png" #마스크 픽셀 복사 
        cv2.copyTo(src, mask1, img)
        cv2.imwrite(j, img)

        k = settings.MEDIA_ROOT+"/test/5.png"
        f1 = np.fromfile(j)
        result = remove(f1)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(k)

        img = Image.open(k)
        os.remove(i)  
        os.remove(j)
        os.remove(k)
        os.remove(result_image1)
        os.remove(result_image2)
        os.remove(initial_image)
        return image_to_bytes(img)
    if style == "PAPRIKA":
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        default_storage.save("test/"+"0.png", img)

        initial_image = "./media/test/0.png"
        result_image1 = "./media/test/1.png"
        result_image2 = settings.MEDIA_ROOT +"/test/2.png"

        f = np.fromfile(initial_image)
        result = remove(f)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(result_image2)

        model = Transformer()
        model.load_state_dict(torch.load('pretrained_model/Paprika_net_G_float.pth'))
        model.eval()

        img_size = 450
        img = cv2.imread('./media/test/0.png')


        T = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(img_size, 2),
            transforms.ToTensor()
        ])

        img_input = T(img).unsqueeze(0)

        img_input = -1 + 2 * img_input

        img_output = model(img_input)

        img_output = (img_output.squeeze().detach().numpy() + 1.) /2.
        img_output = img_output.transpose([1,2,0])
        img_output = cv2.convertScaleAbs(img_output, alpha = (255.0)) 
        cv2.imwrite(result_image1, img_output) 

            #0.png: 원본 사진, 1.png: 그림으로 바뀐 사진 2.png: 배경을 없앤 사진 
        src1 = cv2.imread(result_image2, cv2.IMREAD_UNCHANGED)  #배경 없앤 사진 
        src = cv2.imread(result_image1, cv2.IMREAD_COLOR)        #그림으로 바꾼 사진 
        h, w = img.shape[:2]    #원본 사진의 shape
        h1, w1 = src1.shape[:2]     #배경 없앤 사진의 shape

        if [h,w] != [h1, w1]:
            src1 = cv2.rotate(src1, cv2.ROTATE_90_CLOCKWISE)

        src = cv2.resize(src, dsize=(w, h), interpolation=cv2.INTER_AREA) #원본사진이랑 그림으로 바꾼 사진 크기 맞추기 
        for y in range (h):
            for x in range(w):
                img[y,x] = 255

        mask = src1[:, :, -1] #(1440, 666)
        th, mask1 = cv2.threshold(mask, 2, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        mask1 = cv2.resize(mask1, dsize=(w,h), interpolation=cv2.INTER_AREA )

        i = settings.MEDIA_ROOT +"/test/3.png" #마스크
        cv2.imwrite(i, mask1)

        j = settings.MEDIA_ROOT +"/test/4.png" #마스크 픽셀 복사 
        cv2.copyTo(src, mask1, img)
        cv2.imwrite(j, img)

        k = settings.MEDIA_ROOT +"/test/5.png"
        f1 = np.fromfile(j)
        result = remove(f1)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(k)

        img = Image.open(k)
        os.remove(i)  
        os.remove(j)
        os.remove(k)
        os.remove(result_image1)
        os.remove(result_image2)
        os.remove(initial_image)
        return image_to_bytes(img)
    if style == "SHINKAI":
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        default_storage.save("test/"+"0.png", img)

        initial_image = "./media/test/0.png"
        result_image1 = "./media/test/1.png"
        result_image2 = settings.MEDIA_ROOT +"/test/2.png"

        f = np.fromfile(initial_image)
        result = remove(f)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(result_image2)

        model = Transformer()
        model.load_state_dict(torch.load('pretrained_model/Shinkai_net_G_float.pth'))
        model.eval()

        img_size = 450
        img = cv2.imread(initial_image)


        T = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(img_size, 2),
            transforms.ToTensor()
        ])

        img_input = T(img).unsqueeze(0)

        img_input = -1 + 2 * img_input

        img_output = model(img_input)

        img_output = (img_output.squeeze().detach().numpy() + 1.) /2.
        img_output = img_output.transpose([1,2,0])
        img_output = cv2.convertScaleAbs(img_output, alpha = (255.0)) 
        cv2.imwrite(result_image1, img_output) 


            #0.png: 원본 사진, 1.png: 그림으로 바뀐 사진 2.png: 배경을 없앤 사진                                    #원본 사진 
        src1 = cv2.imread(result_image2, cv2.IMREAD_UNCHANGED)  #배경 없앤 사진 
        src = cv2.imread(result_image1, cv2.IMREAD_COLOR)        #그림으로 바꾼 사진 
        h, w = img.shape[:2]    #원본 사진의 shape
        h1, w1 = src1.shape[:2]     #배경 없앤 사진의 shape

        if [h,w] != [h1, w1]:
            src1 = cv2.rotate(src1, cv2.ROTATE_90_CLOCKWISE)

        src = cv2.resize(src, dsize=(w, h), interpolation=cv2.INTER_AREA) #원본사진이랑 그림으로 바꾼 사진 크기 맞추기 
        for y in range (h):
            for x in range(w):
                img[y,x] = 255

        mask = src1[:, :, -1] 
        th, mask1 = cv2.threshold(mask, 2, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        mask1 = cv2.resize(mask1, dsize=(w,h), interpolation=cv2.INTER_AREA )

        i = settings.MEDIA_ROOT +"/test/3.png" #마스크
        cv2.imwrite(i, mask1)

        j = settings.MEDIA_ROOT +"/test/4.png" #마스크 픽셀 복사 
        cv2.copyTo(src, mask1, img)
        cv2.imwrite(j, img)

        k = settings.MEDIA_ROOT +"/test/5.png"
        f1 = np.fromfile(j)
        result = remove(f1)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(k)

        img = Image.open(k)
        os.remove(i)  
        os.remove(j)
        os.remove(k)
        os.remove(result_image1)
        os.remove(result_image2)
        os.remove(initial_image)
        return image_to_bytes(img)
    else:
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        default_storage.save("test/"+"0.png", img)

        initial_image = settings.MEDIA_ROOT+"/test/0.png"
        result_image = settings.MEDIA_ROOT+"/test/1.png"
        
        f = np.fromfile(initial_image)
        result = remove(f)
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img.save(result_image)

        src1 = cv2.imread("./media/test/1.png", cv2.IMREAD_UNCHANGED)  #배경 없앤 사진 
        src = cv2.imread("./media/test/0.png", cv2.IMREAD_COLOR)        #원본사진 

        h, w = src.shape[:2]    #원본 사진의 shape
        h1, w1 = src1.shape[:2]     #배경 없앤 사진의 shape

        if [h,w] != [h1, w1]:
            src1 = cv2.rotate(src1, cv2.ROTATE_90_CLOCKWISE)
            os.remove(result_image)
            cv2.imwrite(result_image, src1)

        img= Image.open(result_image)

        os.remove(initial_image)
        os.remove(result_image)


        return image_to_bytes(img)

def image_to_bytes(img):
    output = BytesIO()
    img.save(output, format='PNG', quality=100)
    output.seek(0)
    return output
