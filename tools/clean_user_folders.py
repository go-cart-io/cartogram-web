# Remove folders that its name does match any value in string_key column

import os
import shutil
import sys

from sqlalchemy import MetaData, Table, create_engine, select

# Database configuration
DATABASE_URI = os.environ.get("CARTOGRAM_DATABASE_URI", None)
POSTGRES_PASSWORD_FILE = os.environ.get("POSTGRES_PASSWORD_FILE", None)
if not DATABASE_URI:
    print(f"Invalid DATABASE_URI: {DATABASE_URI}")
    sys.exit()
if POSTGRES_PASSWORD_FILE:
    f = open(POSTGRES_PASSWORD_FILE, "r")
    DATABASE_URI = DATABASE_URI.format(f.read())

TABLE_NAME = "cartogram_entry"
COLUMN_NAME = "string_key"
TARGET_DIRECTORY = "/root/internal/static/userdata"
TMP_DIRECTORY = "/root/internal/tmp"


# Create database engine
engine = create_engine(DATABASE_URI)
connection = engine.connect()

# Reflect the table
metadata = MetaData()
table = Table(TABLE_NAME, metadata, autoload_with=engine)

# Query the string_key column
query = select(table.c[COLUMN_NAME])
result = connection.execute(query)
valid_folder_names = {getattr(row, COLUMN_NAME) for row in result}
connection.close()

# Remove folders not in the valid list
for folder_name in os.listdir(TARGET_DIRECTORY):
    folder_path = os.path.join(TARGET_DIRECTORY, folder_name)
    if os.path.isdir(folder_path) and folder_name not in valid_folder_names:
        destination_path = os.path.join(TMP_DIRECTORY, folder_name)
        print(f"Moving folder: {folder_path} -> {destination_path}")
        shutil.move(folder_path, destination_path)
