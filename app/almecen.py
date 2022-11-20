from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

p = SQLAlchemy()

class Pendientes(p.Model):
    __tablename__ = 'pendientes'
    id = p.Column(p.Integer(), primary_key = True)
    padre = p.Column(p.Integer())
    tarea = p.Column(p.String())
    creacion = p.Column(p.DateTime(), default= datetime.now)
    hecho = p.Column(p.Boolean(), default = False)


    def __init__(self,padre, tarea) -> None:
        self.__inicializar__(padre, tarea)



    def __inicializar__(self, padre = None, tarea = None) -> None:
        if type(padre) != int or not tarea: return

        self.padre = padre
        self.tarea = tarea


    def agregarTareaPendiente(self, pendiente :str) -> bool:
        if not self.ref_a_padre or self.ref_a_padre.id != self.padre: return False

        nuevoPendiente = Pendientes(self.ref_a_padre.id, pendiente)
        p.session.add(nuevoPendiente)
        p.session.commit()
        self.ref_a_padre.ids_tareas.append(nuevoPendiente.id)
        return True


    @staticmethod
    def obtenerTareas(lista_id:list) -> list:
        lista = []
        for id in lista_id:
            pendiente = p.session.query(Pendientes).get(id)
            if pendiente:
                lista.append((pendiente.tarea, pendiente.hecho, id))
        return lista
        



    @staticmethod
    def __crear__(app) -> None:
        if not app: return
        p.init_app(app)
        with app.app_context():
            p.create_all()

            

    @staticmethod
    def agregarPendiente(padre, pendiente) -> int or None:
        if type(pendiente) != str: return None

        tareaPendiente = Pendientes(padre, pendiente)

        p.session.add(tareaPendiente)
        p.session.commit()
        return tareaPendiente.id


    @staticmethod
    def eliminar(id : int) -> bool:
        if type(id) != int or id <= 0: False
        p.session.query(Pendientes).filter(Pendientes.id == id).delete()
        p.session.commit()
        return True


    @staticmethod
    def cambiarEstado(padre : object, id : int) -> None:
        tarea = p.session.query(Pendientes).get(id)

        if tarea and tarea.padre == padre.id:

            tarea.hecho = not tarea.hecho
            p.session.add(tarea)
            p.session.commit()

    @staticmethod
    def eliminarPorUsuario(usuario : object)->None:
        usuario.cargarIds()
        for id in usuario.ids_tareas:
            p.session.query(Pendientes).filter(Pendientes.id == id).delete()
        if len(usuario.ids_tareas) > 0:
            p.session.commit()