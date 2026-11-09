"""Carrega a configuração de ambiente; nunca contém credenciais embutidas."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')


class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3307'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'cidadao_app')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'alertabairro')
    APP_ADMIN_KEY = os.getenv('APP_ADMIN_KEY', '')
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 8192
    TESTING = False
