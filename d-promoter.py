from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from datetime import datetime
import os
import secrets, string
from elasticsearch7 import Elasticsearch as Elasticsearch7
import threading
import json
from psycopg2 import pool, errors

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        if record.levelname == 'INFO':
            color_code = '\033[34m' 
        elif record.levelname == 'WARNING':
            color_code = '\033[33m' 
        elif record.levelname == 'DEBUG':
            color_code = '\033[32m'
        elif record.levelname == 'ERROR':
            color_code = '\033[31m' 
        reset_code = '\033[0m'
        
        service_name = "MangoSC"
        domain = "sensor-pf-interaction | SPPIDI_ENV | b-prd"
        container_name = "orch-auth-user"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        action = record.getMessage()

        log_message = (
            f"{log_time}\t{color_code}{record.levelname}{reset_code}\t"
            f"{service_name} | {domain} | - | {container_name} | "
            f"{timestamp} | - | - | {action}"
        )
        
        return log_message

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)

es_host = os.environ.get('ES-HOST', '192.168.15.10')
es_port = os.environ.get('ES-PORT', '9200')
es_index = os.environ.get('ES-INDEX', 'backend')
client = Elasticsearch7([f'http://{es_host}:{es_port}'])

pg_host = os.environ.get('POSTGRES-HOST', 'relacional-database')
pg_port = os.environ.get('POSTGRES-PORT', '5432')
pg_user = os.environ.get('POSTGRES-USER','root')
pg_password = os.environ.get('POSTGRES-PASSWORD','Letr@shop2024')
pg_db_name = os.environ.get('POSTGRES-DB', 'letrashop')

connection_pool = pool.SimpleConnectionPool(1, 20,
    host=pg_host, port=pg_port, user=pg_user, password=pg_password, dbname=pg_db_name)

serviceName = os.environ.get('SVC-NAME', 'd-category')

app = Flask(__name__)

CORS(app)

def generate_tid(length=24):
    characters = string.ascii_uppercase + string.digits
    tid = ''.join(secrets.choice(characters) for _ in range(length))
    return tid

def send_logs_es(doc):
    #client.index(index=es_index, document=doc)
    pass

def get_db_connection():
    connection = connection_pool.getconn()
    return connection

@app.route('/', methods=['DELETE'])
def shipping_cost():
    start_time = datetime.now() 
    message_id = request.headers.get('messageId', generate_tid())
    connection = get_db_connection()
    cursor = connection.cursor()
    
    logger.info(f'{message_id} | - | requestStarting')
    body = request.json
    headers = request.headers
    header_info = ''
    for header, value in headers.items():
        header_info += (f'"{header}":"{value}",')
    logger.info(f'{message_id} | - | requestHeaderReceived | - | {header_info}')    
    doc = {
        'timestamp': datetime.now(),
        'environment': 'b-prd',
        'requestHeaderReceived': header_info,
        'requestMethod': 'DELETE',
        'tid': message_id,
        'serviceName': serviceName,
    }
    thread = threading.Thread(target=send_logs_es, args=(doc,))
    thread.start()
        
    logger.info(f'{message_id} | - | requestBodyReceived | - | {body}')
    doc = {
        'timestamp': datetime.now(),
        'environment': 'b-prd',
        'requestPayloadReceived': json.dumps(body),
        'tid': message_id,
        'serviceName': serviceName,
    }
    thread = threading.Thread(target=send_logs_es, args=(doc,))
    thread.start()
    
    if not body.get('promoter_id'):
        error_message = {'error':'Missing mandatory fields'}
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)  # Calcula o tempo total de execução em ms
        doc = {
            'timestamp': datetime.now(),
            'environment': 'b-prd',
            'requestPayloadReturned': json.dumps({'response':f'{error_message}'}),
            'tid': message_id,
            'serviceName': serviceName,
            'totalTime': total_time,
            'responseHttpStatus': 400
        }
        thread = threading.Thread(target=send_logs_es, args=(doc,))
        thread.start()
        logger.error(f'{message_id} | - | payloadReturn | - | {error_message}')
        logger.error(f'{message_id} | - | httpStatus | - | 400')
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)  # Calcula o tempo total de execução em ms
        logger.info(f'{message_id} | - | totalExecutionTime | - | {total_time} ms')
        return jsonify(error_message), 400  
    
    
    
    logger.debug(f'{message_id} | - | converting body parameters to variables')
    promoter_id = body.get('promoter_id')
    logger.debug(f'{message_id} | - | body converted to variables')

    logger.debug(f'{message_id} | - | deleting from database')
    try:
        cursor.execute(f"DELETE FROM tb_promoter WHERE promoter_id='{promoter_id}'")
        logger.debug(f'{message_id} | - | commiting data')
        connection.commit()
    except Exception as e:
        # Handle other exceptions if necessary
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)  # Calcula o tempo total de execução em ms
        response_message = {'response':f'error get shipping price by this error: {str(e)}'}
        doc = {
            'timestamp': datetime.now(),
            'environment': 'b-prd',
            'requestPayloadReturned': json.dumps(response_message),
            'tid': message_id,
            'serviceName': serviceName,
            'totalTime': total_time,
            'responseHttpStatus': 500
        }
        thread = threading.Thread(target=send_logs_es, args=(doc,))
        thread.start()
        logger.error(f'{message_id} | - | payloadReturn | - | {response_message}')
        logger.error(f'{message_id} | - | httpStatus | - | 500')
        logger.info(f'{message_id} | - | totalExecutionTime | - | {total_time} ms')
        return response_message, 500
    total_time = int((datetime.now() - start_time).total_seconds() * 1000)  # Calcula o tempo total de execução em ms
    doc = {
        'timestamp': datetime.now(),
        'environment': 'b-prd',
        'requestPayloadReturned': '',
        'tid': message_id,
        'serviceName': serviceName,
        'totalTime': total_time,
        'responseHttpStatus': 204
    }
    thread = threading.Thread(target=send_logs_es, args=(doc,))
    thread.start()
    logger.debug(f'{message_id} | - | closing data connection')
    cursor.close()
    connection_pool.putconn(connection)
    logger.info(f'{message_id} | - | payloadReturn | - | ')
    logger.info(f'{message_id} | - | httpStatus | - | 204')
    total_time = int((datetime.now() - start_time).total_seconds() * 1000)  # Calcula o tempo total de execução em ms
    logger.info(f'{message_id} | - | totalExecutionTime | - | {total_time} ms')
    return '', 204 


if __name__ == '__main__':
    ssl_context = ('/app/certs/server.crt', '/app/certs/server.key')  # Caminho para os arquivos SSL
    app.run(host='0.0.0.0', port=5000, ssl_context=ssl_context)