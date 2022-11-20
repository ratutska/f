from flask import Blueprint

autenticacion = Blueprint('autenticacion', __name__, url_prefix = '/autenticaion')

from . import rutas