from .ControladorProjeto import ControladorProjeto

class Main:
    def __init__(self):
        self.controlador = ControladorProjeto()

    def rodar(self):
        self.controlador.executar()