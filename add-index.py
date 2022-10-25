#! python

from collections import defaultdict
from symbol import file_input

import pandas
from numpy import zeros_like
import locale
import ghostscript
import os
import argparse

def get_pdfmark_element(page, title, count=None):

    if count:
        return f"""
[ /Count -{count}
    /Title ({title})
    /Page {page}
    /OUT pdfmark"""

    return f"""
[ /Title ({title})
  /Page {page}
  /OUT pdfmark"""


def get_count(df):
    levels = df.level.to_numpy()

    assert levels[0] == 1, "First level must be 1"
    count = zeros_like(levels)

    curr_levels = defaultdict(lambda: 0)

    for i, lvl in enumerate(levels[1:], 1):

        if lvl > levels[i - 1]:
            curr_levels[lvl] = i - 1
            count[curr_levels[lvl]] = 1
        elif lvl != 1 and lvl == levels[i - 1] and count[i - 1]:
            count[curr_levels[lvl]] += 1
        elif lvl > 1:
            count[curr_levels[lvl]] += 1

    df["count"] = count

    return df


def get_pdfmarks(df):
    return "".join(
        get_pdfmark_element(row.page, row.title, row.count) for row in df.itertuples()
    )

def run_ghostscript(pdfmarks, input_file, output_file):
    with open("pdfmarks", "w") as f:
        f.write(pdfmarks)

    args = [
        "gs",  # actual value doesn't matter
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=pdfwrite",
        f"-sOutputFile={output_file}",
        "./pdfmarks",
        f"{input_file}",
    ]

    encoding = locale.getpreferredencoding()
    args = [a.encode(encoding) for a in args]

    ghostscript.Ghostscript(*args)

    os.remove("pdfmarks")


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--index", help="index file", required=True, type=str)
    parser.add_argument("-o", "--out", help="Output file", required=True, type=str)
    parser.add_argument("-in", "--input", help="Input file", required=True, type=str)

    return parser.parse_args()


if __name__ == "__main__":

    args = get_args()

    file_input = args.input
    if not file_input.endswith(".pdf"):
        file_input += ".pdf"

    if not os.path.exists(file_input):
        raise FileNotFoundError(f"Input file {file_input} not found")

    index = args.index
    if not index.endswith(".csv"):
        index += ".csv"

    if not os.path.exists(index):
        raise FileNotFoundError(f"Index file {index} not found")

    file_output = args.out
    if not file_output.endswith(".pdf"):
        file_output += ".pdf"

    # Load data
    df = pandas.read_csv(index, sep=";", skipinitialspace=True)

    df = get_count(df)

    pdfmarks = get_pdfmarks(df)

    run_ghostscript(pdfmarks, file_input, file_output)
    
