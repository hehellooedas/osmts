import pandas,openpyxl
from pathlib import Path


def excel2csv(ws:openpyxl.worksheet.worksheet.Worksheet,directory:Path):
    data = []
    for row in ws.iter_rows(values_only=True):
        data.append(row)

    df = pandas.DataFrame(data[1:], columns=data[0])
    df.to_csv(directory, index=False, encoding='utf-8')

