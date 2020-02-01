from datetime import datetime

from conf import cluster_conf
from get_data.src import s3_utils, upload_to_db as upload
from get_data.src import es_utils
from conf.cluster_conf import ES_HOST_PORT, ES_HOST_IP

"""
Function test shall be executed in order (from top to bottom)
"""


def test_upload_to_db():
    label_file = "test/resources/labels.json"
    bucket_name = cluster_conf.BUCKET_NAME
    key_prefix = ""
    es_ip_host = cluster_conf.ES_HOST_IP
    es_port_host = cluster_conf.ES_HOST_PORT
    es_index_name = "test_index"
    s3_success, es_success, fail = upload.upload_to_db(label_file, bucket_name, es_ip_host, es_port_host, es_index_name,
                                        key_prefix=key_prefix, overwrite=False)
    assert (s3_success, es_success, fail) == (5, 5, 1)


def test_upload_to_db_overwrite():
    label_file = "test/resources/labels.json"
    bucket_name = cluster_conf.BUCKET_NAME
    key_prefix = ""
    es_ip_host = cluster_conf.ES_HOST_IP
    es_port_host = cluster_conf.ES_HOST_PORT
    es_index_name = "test_index"
    s3_success, es_success, fail = upload.upload_to_db(label_file, bucket_name, es_ip_host, es_port_host, es_index_name,
                                        key_prefix=key_prefix, overwrite=True)
    assert (s3_success, es_success, fail) == (5, 5, 1)


def test_upload_to_db_s3_KO_es_OK():
    es_ip_host = cluster_conf.ES_HOST_IP
    es_port_host = cluster_conf.ES_HOST_PORT
    es_index_name = "test_index"
    es_utils.delete_index(es_index_name, es_ip_host, es_port_host)
    label_file = "test/resources/labels.json"
    bucket_name = cluster_conf.BUCKET_NAME
    key_prefix = ""
    s3_success, es_success, fail = upload.upload_to_db(label_file, bucket_name, es_ip_host, es_port_host, es_index_name,
                                                       key_prefix=key_prefix, overwrite=False)
    assert (s3_success, es_success, fail) == (0, 5, 6)


def test_upload_to_db_cant_overwrite():
    label_file = "test/resources/labels.json"
    bucket_name = cluster_conf.BUCKET_NAME
    key_prefix = ""
    es_ip_host = cluster_conf.ES_HOST_IP
    es_port_host = cluster_conf.ES_HOST_PORT
    es_index_name = "test_index"
    s3_success, es_success, fail = upload.upload_to_db(label_file, bucket_name, es_ip_host, es_port_host, es_index_name,
                                        key_prefix=key_prefix, overwrite=False)
    assert (s3_success, es_success, fail) == (0, 0, 11)


def test_upload_to_db_key_prefix():
    label_file = "test/resources/labels.json"
    bucket_name = cluster_conf.BUCKET_NAME + "/"
    key_prefix = "/weird/path//"
    es_ip_host = cluster_conf.ES_HOST_IP
    es_port_host = cluster_conf.ES_HOST_PORT
    es_index_name = "test_index"
    s3_success, es_success, fail = upload.upload_to_db(label_file, bucket_name, es_ip_host, es_port_host, es_index_name,
                                        key_prefix=key_prefix, overwrite=False)
    assert (s3_success, es_success, fail) == (5, 0, 6)


def test_upload_to_db_single_label():
    label_file = "test/resources/single_label.json"
    bucket_name = cluster_conf.BUCKET_NAME
    key_prefix = ""
    es_ip_host = cluster_conf.ES_HOST_IP
    es_port_host = cluster_conf.ES_HOST_PORT
    es_index_name = "test_index"
    s3_success, es_success, fail = upload.upload_to_db(label_file, bucket_name, es_ip_host, es_port_host, es_index_name,
                                        key_prefix=key_prefix, overwrite=True)
    assert (s3_success, es_success, fail) == (1, 1, 0)


def test_delete_object_in_s3():
    label_file = "test/resources/labels.json"
    bucket_name = cluster_conf.BUCKET_NAME
    key_prefix = ""
    l_label = upload.get_label_list_from_file(label_file)
    id_list = [label["img_id"] for label in l_label]
    s3_resource = s3_utils.get_s3_resource()
    ret = s3_utils.delete_object_s3(s3_resource, bucket_name, key_prefix, id_list)
    assert ret["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_delete_object_in_s3_key_prefix():
    label_file = "test/resources/labels.json"
    bucket_name = cluster_conf.BUCKET_NAME
    key_prefix = "/weird/path//"
    l_label = upload.get_label_list_from_file(label_file)
    id_list = [label["img_id"] for label in l_label]
    s3_resource = s3_utils.get_s3_resource()
    ret = s3_utils.delete_object_s3(s3_resource, bucket_name, key_prefix, id_list)
    assert ret["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_delete_index_es():
    es_ip_host = cluster_conf.ES_HOST_IP
    es_port_host = cluster_conf.ES_HOST_PORT
    es_index_name = "test_index"
    ret = es_utils.delete_index(es_index_name, es_ip_host, es_port_host)
    assert "acknowledged" in ret and ret["acknowledged"] is True


def test_generate_key_prefix_ok():
    date_str = datetime.now().strftime("%Y%m%dT%H-%M-%S-%f")
    date = datetime.now()
    event_name = "event_test"
    l_label = [{"event": event_name, "img_id": 1, "timestamp": date_str},
               {"event": event_name, "img_id": 2, "timestamp": date_str}]
    key = upload.generate_key_prefix(l_label)
    assert key == f'{event_name}/{date.year}{date.month}{date.day}/'


def test_generate_key_prefix_invalid_name():
    event_name = "event test"
    l_label = [{"event": event_name, "img_id": 1}, {"event": event_name, "img_id": 2}]
    key = upload.generate_key_prefix(l_label)
    assert key is None


def test_generate_key_prefix_different_name():
    event_name = "event_test"
    l_label = [{"event": event_name, "img_id": 1}, {"event": event_name + "_2", "img_id": 2}]
    key = upload.generate_key_prefix(l_label)
    assert key is None


def test_create_index():
    index = "test_create_index"
    create_success = es_utils.create_patate_db_index(host_ip=ES_HOST_IP, host_port=ES_HOST_PORT, index_name=index)
    assert create_success is not None
    del_success = es_utils.delete_index(index=index, host_ip=ES_HOST_IP, port=ES_HOST_PORT)
    assert del_success is not None


if __name__ == "__main__":
    test_delete_index_es()

