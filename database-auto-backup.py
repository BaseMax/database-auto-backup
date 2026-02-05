import os
import subprocess
import logging
import shutil
from typing import List, Dict, Optional
import datetime
import zipfile
import gzip
import bz2
import requests
import pymysql
from pathlib import Path

# ---------------------- CONFIG ----------------------
config: Dict[str, any] = {
    'databases': [
        {
            'name': 'bsafeg_bsafegroup.be',
            'user': 'bsafeg_bsafegroup_be',
            'pass': 'Cm%ld].7WKS.?oQA',
            'host': '127.0.0.1',
            'port': 3306
        },
        {
            'name': 'bsafeg_mazijna.com',
            'user': 'bsafeg_mazijna_com',
            'pass': '~3#9{GuVG]WpJv(A',
            'host': '127.0.0.1',
            'port': 3306
        },
    ],
    'output_dir': './backups',
    'use_mysqldump': True,
    'disable_compression': False,
    'compression': 'gz',  # gz, bz2, zip
    'disable_telegram': False,
    'telegram': {
        'bot_token': '8373765950:AAE3QWYPY1m6ahSJ09UsaeFNzgxyXTp38rc',
        'chat_id': '-1003853984009',
        'caption': 'Auto DB Backup',
    },
    'retention_days': 10,
    'cleanup_after_upload': False,
    'log_file': './backups/backup.log',
}
# -------------------- END CONFIG --------------------

# -------------------- LOGGING ----------------------
logging.basicConfig(filename=config['log_file'], level=logging.INFO)

def logmsg(msg: str) -> None:
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {msg}"
    logging.info(log_message)
    print(log_message)


# -------------------- HELPERS ----------------------
def is_exec_available() -> bool:
    return shutil.which("mysqldump") is not None


def dump_command_available() -> Optional[str]:
    if is_exec_available():
        return 'mysqldump'
    return None


def write_temp_my_cnf(host: str, user: str, password: str, port: int = 3306) -> str:
    tmp_file = Path("/tmp") / f"mycnf_{datetime.datetime.now().timestamp()}"
    content = f"[client]\nuser={user}\npassword={password}\nhost={host}\nport={port}\n"
    tmp_file.write_text(content)
    tmp_file.chmod(0o600)
    return str(tmp_file)


# -------------------- DATABASE DUMP ----------------------
def run_single_dump(db_config: Dict[str, any], out_sql_path: str) -> bool:
    dump_cmd = dump_command_available()
    if dump_cmd:
        tmp_ini = write_temp_my_cnf(db_config['host'], db_config['user'], db_config['pass'], db_config['port'])
        cmd = [
            dump_cmd,
            f"--defaults-extra-file={tmp_ini}",
            "--routines", "--triggers", "--events", "--single-transaction", "--quick",
            "--skip-lock-tables", "--add-drop-database",
            db_config['name']
        ]
        try:
            logmsg(f"Running dump for {db_config['name']} using {dump_cmd}...")
            subprocess.run(cmd, check=True, stdout=open(out_sql_path, 'w'), stderr=subprocess.PIPE)
            os.remove(tmp_ini)
            return True
        except subprocess.CalledProcessError as e:
            logmsg(f"ERROR: Dump failed for {db_config['name']}, error: {e}")
            return False
    else:
        logmsg(f"Exec not available or mysqldump disabled. Using Python fallback for {db_config['name']}...")
        return php_dump_database(db_config, out_sql_path)


def php_dump_database(db_config: Dict[str, any], out_file: str) -> bool:
    try:
        conn = pymysql.connect(
            host=db_config['host'], user=db_config['user'], password=db_config['pass'],
            database=db_config['name'], port=db_config['port'], charset='utf8mb4'
        )
        cursor = conn.cursor()
        sql_dump = f"-- Backup of database {db_config['name']}\n-- Generated on {datetime.datetime.now()}\n\n"
        
        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_table = cursor.fetchone()[1]
            sql_dump += create_table + ";\n\n"
            
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            for row in rows:
                values = ','.join(f'"{str(v)}"' if v is not None else 'NULL' for v in row)
                sql_dump += f"INSERT INTO `{table_name}` VALUES ({values});\n"
            
            sql_dump += "\n"
        
        with open(out_file, 'w') as f:
            f.write(sql_dump)
        
        conn.close()
        return True
    except Exception as ex:
        logmsg(f"ERROR: {str(ex)}")
        return False


# -------------------- COMPRESSION ----------------------
def compress_file(path: str, compression_type: str = 'gz') -> Optional[str]:
    if not os.path.exists(path):
        return None
    
    if compression_type == 'gz':
        with open(path, 'rb') as f_in:
            with gzip.open(f'{path}.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return f'{path}.gz'
    
    elif compression_type == 'bz2':
        with open(path, 'rb') as f_in:
            with bz2.BZ2File(f'{path}.bz2', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return f'{path}.bz2'
    
    elif compression_type == 'zip':
        with zipfile.ZipFile(f'{path}.zip', 'w') as zipf:
            zipf.write(path, os.path.basename(path))
        return f'{path}.zip'
    
    return None


# -------------------- TELEGRAM ----------------------
def upload_to_telegram(file_path: str, token: str, chat_id: str, caption: str = '') -> bool:
    if not os.path.exists(file_path):
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    files = {'document': open(file_path, 'rb')}
    data = {'chat_id': chat_id, 'caption': caption}
    
    try:
        response = requests.post(url, files=files, data=data)
        files['document'].close()
        if response.status_code == 200:
            return True
        else:
            logmsg(f"Telegram upload failed: {response.text}")
            return False
    except requests.RequestException as e:
        logmsg(f"Telegram upload error: {str(e)}")
        return False


# -------------------- RETENTION ----------------------
def cleanup_old_backups(retention_days: int, output_dir: str) -> None:
    cut_off_time = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    for file in Path(output_dir).glob('*'):
        if file.is_file() and file.stat().st_mtime < cut_off_time.timestamp():
            file.unlink()


# -------------------- MAIN ----------------------
def main():
    date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    final_files = []

    os.makedirs(config['output_dir'], exist_ok=True)

    for db in config['databases']:
        file_name = f"backup_{db['name']}_{date}.sql"
        sql_path = os.path.join(config['output_dir'], file_name)
        
        if run_single_dump(db, sql_path):
            final_file = sql_path
            if not config['disable_compression']:
                compressed_file = compress_file(sql_path, config['compression'])
                if compressed_file:
                    final_file = compressed_file
                    os.remove(sql_path)
            final_files.append(final_file)
            logmsg(f"Backup created: {final_file}")

    if not config['disable_telegram']:
        for file_path in final_files:
            db_name = Path(file_path).stem.split('_')[1]
            caption = f"📦 Auto Database Backuper\n🗄 Database: {db_name}\n⏰ Date & Time: {datetime.datetime.now().strftime('%A, %B %d, %Y, %H:%M:%S %Z')}\n"
            if not upload_to_telegram(file_path, config['telegram']['bot_token'], config['telegram']['chat_id'], caption):
                logmsg(f"Failed to upload {file_path} to Telegram")

    if config['retention_days'] > 0:
        cleanup_old_backups(config['retention_days'], config['output_dir'])

    if config['cleanup_after_upload']:
        for file_path in final_files:
            os.remove(file_path)
    
    logmsg("Backup job finished.")


if __name__ == "__main__":
    main()
