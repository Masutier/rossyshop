import os
from datetime import datetime

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
formatted_date = datetime.today()
fecha = formatted_date.strftime("%b %d %Y %H:%M")


def crearFolder(destiny_path, fileNamex, month):
    os.makedirs(destiny_path + fileNamex[0] + "_" + month)
    endDir = destiny_path + fileNamex[0] + "_" + month
    return endDir


def clean_file(dataframe):
    """Clean column names in a dataframe"""
    dataframe.columns = [
        col.upper()
        .replace(" ", "_").replace("-", "_").replace("$", "").replace("?", "")
        .replace("%", "").replace(".", "").replace("Á", "A").replace("É", "E")
        .replace("Í", "I").replace("Ó", "O").replace("Ò", "O").replace("Ú", "U").replace("Ñ", "N")
        .replace("á", "A").replace("é", "E").replace("í", "I").replace("ó", "O")
        .replace("ú", "U").replace("ñ", "N").replace("@", "").replace("#", "")
        .replace("/", "").replace("\\", "").replace("(", "").replace(")", "")
        for col in dataframe.columns
    ]

    # for col in dataframe.columns:
    #     dataframe[col] = dataframe[col].ffill() # Replaces the empty cell with the value from the cell above
    
    return dataframe
