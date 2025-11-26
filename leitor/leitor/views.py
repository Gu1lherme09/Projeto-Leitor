
from django.shortcuts import render

def inicio(request):
    return render(request,"home/home.html")

def pesquisar(request):
    return render(request,"abas/buscar_arquivos.html")

def duplicados(request):
    return render(request,"abas/duplicados.html")