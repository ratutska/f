from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.security import check_password_hash, generate_password_hash
from .almecen import Pendientes

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer(), primary_key=True)
    nombre = db.Column(db.String(50), unique = True)
    email = db.Column(db.String(), unique = True)
    password = db.Column(db.String())
    creacion = db.Column(db.DateTime(), default = datetime.now)
    pendientes = db.Column(db.String(), unique = True)
    tareas_cargadas = False
    autenticado = False
    lista_tareas = None
    ids_tareas = None


    def __init__(self, nombre:str, email:str, password:str) -> None:
        self.__inicializar__(nombre, email, password)

    def __init__(self, usuario_dic:dict) -> None:
        if type(usuario_dic) != dict:
            self.__inicializar__()
            return
        try:
            self.__inicializar__(usuario_dic['nombre'],usuario_dic['email'],usuario_dic['password'])
        except KeyError:
            self.__inicializar__()



    def __inicializar__(self, nombre = None, email = None, password = None) -> None:

        if type(nombre) != str or type(email) != str or type(password) != str:
            self.nombre = None
            self.email = None
            self.password = None
            self.autenticado = False
            return

        self.nombre = nombre
        self.email = email
        self.password = generate_password_hash(password)
        self.autenticado = True



    def actualizar(self, nombre:str = None, email:str = None, password:str = None) -> None:
        if nombre:
            self.nombre = nombre
        if email:
            self.email = email
        if password:
            self.password = generate_password_hash(password)
            
        db.session.add(self)
        db.session.commit()

    def usuarioValido(self) -> bool:
        return self.nombre and self.password and self.email

    def validarPassword(self, password:str) -> bool:
        self.autenticado = check_password_hash(self.password,password)
        return self.autenticado

    def json(self) -> str:
        __jason = '"%s_%i" : {\n"id" : "%i",\n"nombre" : "%s",\n"email" : "%s",\n"password" : "%s",\n"creacion" : "%s",\n"Pendientes" : %s,\n'%\
                (self.__tablename__, self.id, self.id, self.nombre, self.email, self.password, self.creacion, self.pendientes)
        tareas = '"tareas" : {\n' + ','.join(self.lista_tareas)

        __jason += tareas + '\n}\n}'
        return __jason

    def is_authenticated(self) -> bool: #obligatorio para flask-login
         return self.autenticado


    def agregarPendiente(self, pendiente:str) -> None:
        if type(pendiente) != str: return
        self.cargarIds()

        id = Pendientes.agregarPendiente(self.id, pendiente)
        self.ids_tareas.append(id)
        self.pendientes = ','.join( [str (STR) for STR in self.ids_tareas])
        print(f'nueva tarea introducida: {pendiente}')
        self.actualizar()


    def actualizar(self):
        try:
            db.session.add(self)
            db.session.commit()
        except TypeError:
            return

    def cargarIds(self):
        if self.ids_tareas: return
        self.ids_tareas = []
        
        if self.pendientes:
            lista_de_id = self.pendientes.split(',')
            for num in lista_de_id:
                self.ids_tareas.append(int(num))


    def cargarPendientes(self):
        if self.tareas_cargadas or self.lista_tareas:
            self.tareas_cargadas = True
            return
        self.cargarIds()
        self.lista_tareas = Pendientes.obtenerTareas(self.ids_tareas)
        self.tareas_cargadas = True

    
    def eliminarPendiente(self, id : int) -> None:
        self.cargarIds()
        try:
            self.ids_tareas.pop(self.ids_tareas.index(id))
            if not Pendientes.eliminar(id): return
            self.pendientes = ','.join( [str (STR) for STR in self.ids_tareas])
            self.actualizar()
        except:
            return
        

    @staticmethod
    def __crear__(app) -> None:
        db.init_app(app)
        with app.app_context():
            db.create_all()

        Pendientes.__crear__(app)



    @staticmethod
    def agregarListaDeUsuarios(lista : list or tuple) -> bool:
        if type(lista) != list and type(lista) != tuple: return False

        for usuario in lista:
            if type(usuario) == dict:
                usuario = Usuario(usuario)
            if usuario.usuarioValido():
                db.session.add(usuario)

        try:
            db.session.commit()
            ok = True
        except (IntegrityError, OperationalError):
            ok = False
        finally:
            return ok



    @staticmethod
    def agregarUsuarios(*argc : dict or object) -> bool:
        return Usuario.agregarListaDeUsuarios(argc)



    @staticmethod
    def dameTodo() -> object:
        return db.session.query(Usuario).all()



    @staticmethod
    def obtenerPorId(id : int) -> object:
        if type(id) != int or id <= 0:
            id = 1
        return db.session.query(Usuario).get(id)



    @staticmethod
    def obtenerPorEmail(email : str) -> object or None:
        return db.session.query(Usuario).filter_by(email = email).first()



    @staticmethod
    def obtenerPorNombre(nombre : str)-> object or None:
        return db.session.query(Usuario).filter_by(nombre = nombre).first()



    @staticmethod
    def logearse(usuario_dic : dict) -> object or None:
        if type(usuario_dic) != dict: return None
        try:
            validar_nombre = Usuario.obtenerPorNombre(usuario_dic['nombre'])

            usuario = validar_nombre if validar_nombre else Usuario.obtenerPorEmail(usuario_dic['email'])

            if usuario and usuario.validarPassword(usuario_dic['password']):
                return usuario
        except KeyError:
            return None

        return None



    @staticmethod
    def validarRegistroDeDatos(usuario_dic : dict) -> bool:
        try:
            datos = db.session.query(Usuario).filter_by(nombre = usuario_dic['nombre'],email = usuario_dic['email']).first()
            return not datos
        except KeyError:
            return False

    @staticmethod
    def eliminarUsuario(usuario : object):
        Pendientes.eliminarPorUsuario(usuario)
        db.session.query(Usuario).filter(Usuario.id == usuario.id).delete()
        db.session.commit()


    @staticmethod
    def idsDeTareasPendientes(usuario : object) -> list or None:
        if not usuario: return None
        


    @staticmethod
    def guardarListaDeId(usuario : object) -> bool:
        
        if not usuario: return False

        try:
            str_lista = usuario.ids_tareas.join(',')
            usuario.pendientes = str_lista
            return True
        except TypeError: return False

    @staticmethod
    def cargarDependenciaUsuario(usuario : object) -> object or None:
        if not usuario: return None

        
