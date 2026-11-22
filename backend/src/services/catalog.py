from src.models.db import rows


def catalog(cursor):
    return {
        'halls': rows(cursor, 'SELECT code,name,manager,purpose FROM halls ORDER BY code'),
        'instruments': rows(cursor, 'SELECT code,name,unit FROM instruments ORDER BY FIELD(code, "SHENG", "DRUM", "GONG"), code'),
    }


def audit(cursor, actor, action, target):
    cursor.execute('INSERT INTO audit_log(actor,action,target) VALUES (%s,%s,%s)', (actor, action, str(target)))
