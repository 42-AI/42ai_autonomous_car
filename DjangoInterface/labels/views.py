from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import os
from PIL import Image
import json

from .forms import PhotoForm
from .models import Photo

class uploadView(View):
    
    def get(self, request):
        photos_list = Photo.objects.filter(owner=self.request.user).order_by('file')
        return render(self.request, 'labels/labels.html', {'photos': photos_list})

    def post(self, request):
        form = PhotoForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.owner = self.request.user
            photo.file.name = photo.owner.username + '/' + photo.file.name
            photo.save()
            data = {'is_valid': True, 'name': photo.file.name, 'url': photo.file.url}
        else:
            data = {'is_valid': False}
        return JsonResponse(data)

@login_required
def delete_all(request):
    if request.method == 'POST':
        photos_list = Photo.objects.filter(owner=request.user)
        for item in photos_list:
            try:
                os.remove(item.file.name)
            except:
                pass
        photos_list.delete()
    return redirect('/labels/')