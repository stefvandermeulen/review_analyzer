""" File Management """
import datetime
import os
import re
import sys

import dateutil
import numpy as np
import pandas as pd

from collections import Iterable

from sklearn.externals import joblib
from src.utils.logger import Logger

VERBOSE = True
PATH_HOME = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SEP = ';'  # Separator for reading and writing
DTYPE_DEFAULT = {
    "ReviewFeedbackPos": int,
    "ReviewFeedbackNeg": int,
    "ReviewFeedbackScore": int
}


def create_dir(*args):
    folderpath = os.path.join(*args)
    if os.path.exists(folderpath) and os.path.isfile(folderpath):
        Logger().info("Warning: {} was a file (replaced it with a folder)".format(folderpath))
        os.remove(folderpath)

    if not os.path.exists(folderpath):
        os.makedirs(folderpath)
    return folderpath


def create_file(*args):
    path_file = os.path.join(*args)
    path_folder = os.path.dirname(path_file)
    create_dir(path_folder)
    return path_file


def get_filepath(folderpath, filename):
    return os.path.join(folderpath, filename)


def file_exists(filepath):
    return os.path.isfile(filepath)


def find_file(folderpath, regex=r'.csv'):
    list_of_files = []
    list_of_unsorted_files = os.listdir(folderpath)
    for filename in list_of_unsorted_files:
        if re.search(regex, filename):
            list_of_files.append(filename)
    sorted(list_of_files)
    return get_filepath(folderpath, list_of_files[-1])


def get_files_matching(folderpath, regex=r'.csv'):
    create_dir(folderpath)
    files = os.listdir(folderpath)
    files = [get_filepath(folderpath, f) for f in files if re.search(regex, f)]
    files.sort(key=lambda x: os.path.getmtime(x))
    return files


def get_basename(filepath):
    return os.path.basename(filepath)


def filepath_to_railobj(filepath):
    railobjectid = re.findall(r'(\d+)[^.\/\\]*.csv', filepath)[-1]
    return railobjectid


def remove_files_in_folder(folderpath):
    create_dir(folderpath)
    list_of_files = os.listdir(folderpath)
    for filename in list_of_files:
        filepath = get_filepath(folderpath, filename)
        remove(filepath)


def remove(file_path: str):
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
            Logger().info("Removed {}".format(file_path))
        except:
            error_message = 'Unable to remove {}'.format(file_path)
            Logger().info(error_message, file=sys.stderr)
    else:
        Logger().info("Unable to remove {}".format(file_path))


def feature_files(default_path=os.path.join(PATH_HOME, 'data', 'saved'), default_path_prio=False):
    files = {}
    path_strukton_data = os.environ['STRUKTON_DATA'] if (not default_path_prio and
                                                         'STRUKTON_DATA' in os.environ) else default_path
    for rail_id in os.listdir(path_strukton_data):
        if os.path.isdir(os.path.join(path_strukton_data, rail_id)):
            file = os.path.join(path_strukton_data, rail_id, 'features.csv')
            if os.path.exists(file):
                files[rail_id] = file
    return files


""" Parse files """


def col_number(h, col_name):
    h = [v.strip() for v in h]
    col_name = col_name.strip()
    return h.index(col_name)


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def str2datetime(v):
    if type(v) == pd.Timestamp:
        return v.to_datetime()
    if type(v) == datetime.date:
        return datetime.datetime.combine(v, datetime.datetime.min.time())
    if type(v) == str:
        try:
            # 01/02/2016 should be parsed as February 1st, 2016/01/02 should be parsed as January 2th
            splitter = '/' if '/' in v else '-'
            year_first = len(v.split(splitter)[0]) == 4
            day_first = not year_first
            a = dateutil.parser.parse(v, dayfirst=day_first)
            return a
        except ValueError:
            return np.nan
    return np.nan


def str2date(v):
    if type(v) == datetime.date:
        return v
    dt = str2datetime(v)
    if type(dt) != datetime.datetime:
        return dt
    return dt.date()


def str2datestr(v):
    """
    String of a date to string in standard date format
    """
    return str(str2date(v))


""" Read and Write CSVs for Pandas """


def round_as_str(val):
    if not isinstance(val, float):
        return str(val)
    return '{:.3}'.format(val)


def convert_values(val):
    if '|' in val:
        return [float(v) for v in val.strip().split("|")]
    return [float(v) for v in val[1:-1].strip().split(',')]


def convert_datetime(val):
    return str2datetime(val)


def convert_date(val):
    return str2date(val)


def convert_time(val):
    return str2datetime(val).time()


def read_pandas(path: str, sep: str = SEP, verbose: bool = True, dtype: dict = {}, **kwargs):
    """
    Read file and return as pandas dataframe

    Default dtypes for known columns are specified in this function, for optimization and data consistency,
    but can be overridden using the dtype argument.
    """

    if not os.path.isfile(path):
        return pd.DataFrame([])

    c1 = {"Date": convert_date}

    for k, v in DTYPE_DEFAULT.items():
        dtype[k] = dtype[k] if k in dtype else v
    if verbose:
        Logger().info('Read csv: %s' % path)

    df = pd.read_csv(path, sep=sep, converters=c1, dtype=dtype, **kwargs)

    return df


def write_pandas(df: pd.DataFrame, path: str, name: str = None, sep: str = SEP, round_floats: bool = True,
                 header: bool = True,
                 mode: str = "w"):
    """
    Write dataframe to pandas.

    Keyword arguments:
    path -- Folder path if name is not None,
            File path if name is None
    name -- Path to file inside folderpath.
            If none, then path should speficy the file
    round_floats -- round the columns containing floats to 3 decimals
    """
    if name is not None:
        if name[-4:] != '.csv':
            name += '.csv'
        filepath = get_filepath(path, name)
    else:
        filepath = path

    if not isinstance(df, pd.DataFrame) or df.empty:
        Logger().info("Warning: could not write empty df to {}".format(filepath))
        return

    if round_floats:
        cols_float = df.select_dtypes(include=['floating']).columns.values
        df[cols_float] = df[cols_float].round(3)

    if os.path.dirname(path) != '' and not os.path.isdir(os.path.dirname(path)):
        create_dir(os.path.dirname(path))
    if not df.empty and 'MeasurementData' in df and isinstance(df.iloc[0]['MeasurementData'], Iterable):
        df = df.copy()
        df['MeasurementData'] = df['MeasurementData'].apply(lambda l: '|'.join(map(str, l)))

    for k, v in DTYPE_DEFAULT.items():
        if k in df.columns:
            if not df[k].isnull().any():
                df[k] = df[k].astype(v)

    Logger().info("Writing csv to {}".format(os.sep.join(os.path.normpath(path).split(os.sep)[-3:])))
    df.to_csv(filepath, sep=sep, index=False, float_format='%.3f', header=header, mode=mode)


def write_model(model: object, path: str):
    """
    Pickle model
    """
    if path[-4:] != ".pkl":
        path += ".pkl"

    if os.path.dirname(path) != "" and not os.path.isdir(os.path.dirname(path)):
        create_dir(os.path.dirname(path))
    Logger().info("Pickle model to {}".format(os.sep.join(os.path.normpath(path).split(os.sep)[-3:])))
    joblib.dump(value=model, filename=path)


def write_text_file(content: object, folder_path: str, name: str):
    # Add .txt, if not added. Name can be a RailObjectID
    if name[-4:] != '.txt':
        name += '.txt'
    file_path = get_filepath(folder_path, name)
    Logger().info('Write txt:', file_path)
    text_file = open(file_path, "w")
    text_file.write(content)
    text_file.close()


def read_detections_file(path, **kwargs):
    df = read_pandas(path=path, **kwargs)
    return df.fillna(value=.0)
