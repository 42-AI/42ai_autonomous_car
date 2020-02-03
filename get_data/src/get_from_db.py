from pathlib import Path
import json
from tqdm import tqdm

from get_data.src import es_utils
from get_data.src import s3_utils
from conf.cluster_conf import ES_INDEX, ES_HOST_IP, ES_HOST_PORT


def get_missing_picture(picture_dir, l_wanted_pic):
    """
    Look in 'picture_dir' for the pictures listed in 'l_wanted_pic'.
    Return the list of missing pic id.
    :param picture_dir:         [string]        Path to the directory where to look for the pictures
    :param l_wanted_pic:        [list of dict]  List of wanted pictures as follow:
                                                [
                                                    {
                                                        "img_id": "id",
                                                        "file_name": "pic_file_name.jpg",
                                                        "location": "s3_bucket_path"
                                                    },
                                                    ...
                                                ]
    :param verbose:             [int]           Level of verbosity
    :return:                    [list of dict] List of missing picture as dict (same format as l_wanted_pic)
    """
    picture_dir = Path(picture_dir)
    l_missing_pic = []
    for wanted_pic in l_wanted_pic:
        pic_path = picture_dir / wanted_pic["file_name"]
        if not pic_path.is_file():
            l_missing_pic.append(wanted_pic)
    return l_missing_pic


def find_picture_in_db(json_file, output=None, es_index=ES_INDEX, verbose=1):
    """
    Search picture in the database according to a json_file describing the query and return the list of matching pics.
    :param json_file:       [string]        Path to the search description file, json format
    :param output:          [string]        Path to directory where to save the list of picture
    :param es_index:        [string]        Name of the index
    :param verbose:         [int]           verbosity level
    :return:                [list of dict]  List of pictures as dictionary as follow:
                                            {
                                                "img_id": id,
                                                "file_name": "pic_file_name.jpg",
                                                "location": "s3_bucket_path"
                                            }
                            [None]          Return None on error.
    """
    with Path(json_file).open(mode='r', encoding='utf-8') as fp:
        d_query = json.load(fp)
    es = es_utils.get_es_session(host_ip=ES_HOST_IP, port=ES_HOST_PORT)
    if es is None:
        return None
    search_obj = es_utils.get_search_query_from_dict(es_index, d_query)
    response = es_utils.run_query(es, search_obj)
    if verbose > 0:
        print(f'Query sent to {ES_HOST_IP}:{ES_HOST_PORT}')
        if verbose > 1:
            print(f'{search_obj.to_dict()}')
        print(f'Query return successfully: {response.success()}')
    if response.hits.total.relation != "eq":
        print(f'WARNING: you hit the maximum number of result limits: the picture list might not be complete.')
    list_of_pic = [{"img_id": pic.img_id, "file_name": pic.file_name, "location": pic.location} for pic in response]
    if output is not None:
        with Path(output).open(mode='w', encoding='utf-8') as fp:
            json.dump(list_of_pic, fp)
        if verbose > 0:
            print(f'Result written to "{Path(output)}"')
    return list_of_pic


def search_and_download(query_json, picture_dir, es_index=ES_INDEX, force=False, verbose=1):
    """
    Search picture in the database according to a query_json file describing the query and download the picture
    not found in the picture_dir. Missing pictures are download to this same picture_dir.
    A picture is missing if the "file_name", as stored in the db, can't be found in picture_dir.
    :param query_json:      [string]        Path to the search description file, json format
    :param picture_dir:     [string]        Path to the picture directory
    :param es_index:        [string]        Name of the index
    :param force:           [int]           If True, will NOT prompt user for validation before download.
    :param verbose:         [int]           Verbosity level
    :return:                [list of dict]  List of downloaded pictures as dictionary as follow:
                                            {
                                                "img_id": id,
                                                "file_name": "pic_file_name.jpg",
                                                "location": "s3_bucket_path"
                                            }
                            [None]          Return None on error.
    """
    picture_dir = Path(picture_dir)
    print(f'Searching for picture in "{es_index}" index')
    l_picture = find_picture_in_db(json_file=query_json, es_index=es_index, verbose=verbose)
    if l_picture is None:
        return None
    l_missing_pic = get_missing_picture(picture_dir, l_picture)
    print(f'{len(l_picture)} picture(s) found matching the query')
    print(f'{len(l_missing_pic)} picture missing in "{picture_dir}" shall be downloaded.')
    if not force:
        proceed = None
        while proceed not in ["y", "n"]:
            proceed = input(f'Do you want to proceed and download the {len(l_missing_pic)} missing picture(s) (y/n)? ')
        if proceed == "n":
            return []
    print("Downloading...")
    for picture in tqdm(l_missing_pic):
        output_file = picture_dir / picture["file_name"]
        s3_utils.download_from_s3(picture["img_id"], picture["location"], output_file.as_posix())
    print(f'Pictures have successfully been downloaded to "{picture_dir}"')
    return l_missing_pic