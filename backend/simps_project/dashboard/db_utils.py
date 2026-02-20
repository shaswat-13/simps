# db_utils.py
import psycopg2
import psycopg2.extras
from django.conf import settings

def get_db_connection():
    connection = psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        sslmode='require'  # required for Supabase
    )
    return connection

def execute_query(query, params=None, fetch=False):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            if query.strip().upper().startswith("INSERT"):
                try:
                    return cursor.fetchone()['id']
                except:
                    return None
            return None
    
    except Exception as e:
        connection.rollback()
        raise e
    
    finally:
        cursor.close()
        connection.close()
