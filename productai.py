# -*- coding=utf8 -*-
import os
import csv
import tempfile
import json
import datetime as dt
from contextlib import contextmanager

import six
import requests
from requests.adapters import HTTPAdapter

__all__ = ['Client']

SIGNATURE_LEN = 32
API_URL = os.environ.get('PRODUCTAI_API_URL', 'https://api.productai.cn')
API_VERSION = '1'


class Client(object):

    def __init__(self, access_key_id, access_key_secret,
                 session=None, url_root=API_URL):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        if not session:
            session = get_default_session()
        self.session = session
        self.lang = 'en-us'
        self.url_root = url_root

    def get_api(self, type_, id_):
        return API(self, type_, id_)

    def get_image_search_api(self, id_):
        return API(self, 'search', id_)

    def get_batch_api(self):
        return BatchAPI(self)

    def get_image_set_creating_api(self):
        return ImageSetAPI(self)

    def get_image_set_api(self, image_set_id=None):
        return ImageSetAPI(self, image_set_id)

    def get_customer_service_api(self, service_id=None):
        return CustomerServiceAPI(self, service_id)

    def get_color_analysis_api(self, sub_type):
        return ColorAnalysisAPI(self, sub_type)

    def get(self, api_url, **kwargs):
        headers = self.get_headers()
        resp = self.session.get(
            api_url,
            headers=headers,
            timeout=30,
            **kwargs
        )
        return resp

    def post(self, api_url, data=None, json=None, files=None, timeout=30):
        headers = self.get_headers()
        resp = self.session.post(
            api_url,
            data=data,
            json=json,
            headers=headers,
            files=files,
            timeout=timeout
        )
        return resp

    def put(self, api_url, data=None, json=None, timeout=30):
        headers = self.get_headers()
        resp = self.session.put(
            api_url,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout
        )
        return resp

    def delete(self, api_url, **kwargs):
        headers = self.get_headers()
        resp = self.session.delete(
            api_url,
            headers=headers,
            timeout=30,
            **kwargs
        )
        return resp

    def get_auth_headers(self):
        headers = make_auth_headers(self.access_key_id)
        return headers

    def set_lang(self, lang):
        self.lang = lang

    def get_headers(self):
        headers = self.get_auth_headers()
        if self.lang:
            headers['Accept-Language'] = self.lang
        return headers


class API(object):

    def __init__(self, client, type_, id_):
        self.client = client
        self.type_ = type_
        self.id_ = id_
        self.url_root_ = API_URL

    def query(self, image, loc='0-0-1-1', count=20, tags=None, **kwargs):
        data = {
            'loc': loc,
            'count': count,
        }

        if tags:
            if isinstance(tags, six.string_types):
                data['tags'] = tags
            elif isinstance(tags, list):
                data['tags'] = '|'.join(tags)
            elif isinstance(tags, dict):
                data['tags'] = json.dumps(tags)

        files = None
        if isinstance(image, six.string_types):
            data['url'] = image
        elif hasattr(image, 'read'):
            files = {'search': image}

        if kwargs:
            bad_keys = [k for k in ['url', 'search'] if k in kwargs]
            if len(bad_keys) > 0:
                raise ValueError('The keys %r are in conflict with built-in parameters.' % bad_keys)
            data.update(kwargs)

        return self.client.post(self.base_url, data=data, files=files)

    @property
    def base_url(self):
        return '/'.join([self.client.url_root, self.type_, self.id_])


class ColorAnalysisAPI(API):
    SUBTYPE_SERVICE_IDS = {
        'everything': '_0000072',
        'foreground': '_0000073',
        'person_outfit': '_0000074',
    }
    GRANULARITIES = ['major', 'detailed', 'dominant']
    RETURN_TYPES = ['basic', 'w3c', 'ncs', 'cncs']

    def __init__(self, client, sub_type):
        try:
            service_id = self.SUBTYPE_SERVICE_IDS[sub_type]
        except KeyError:
            raise TypeError(
                "%r is not one of the valid subtypes: %r" %
                (sub_type, list(self.SUBTYPE_SERVICE_IDS))
            )
        super(ColorAnalysisAPI, self).__init__(
            client, 'color', service_id)
        self.sub_type = sub_type

    def query(self, image, granularity, return_type, loc='0-0-1-1'):
        if granularity not in self.GRANULARITIES:
            raise TypeError(
                "%r is not one of the valid granularities: %r" %
                (granularity, self.GRANULARITIES)
            )
        if return_type not in self.RETURN_TYPES:
            raise TypeError(
                "%r is not one of the valid return types: %r" %
                (return_type, self.RETURN_TYPES)
            )
        data = {
            'loc': loc,
            'granularity': granularity,
            'return_type': return_type,
        }

        files = None
        if isinstance(image, six.string_types):
            data['url'] = image
        elif hasattr(image, 'read'):
            files = {'image': image}

        return self.client.post(self.base_url, data=data, files=files)


class BatchAPI(API):

    def __init__(self, client):
        self.client = client
        self.type_ = 'batch'
        self.id_ = '_1000001'

    def query(self, *args, **kwargs):
        raise NotImplementedError()

    def prepare_by_file(self, service_id, tf):
        endpoint = self.base_url + '/task/prepare'
        return self.client.post(
            endpoint,
            data={'service_id': service_id},
            files={'urls': tf},
            timeout=1800
        )

    def prepare(self, service_id, images_infos):
        with tempfile.NamedTemporaryFile() as tf:
            writer = csv.writer(tf)
            writer.writerows(images_infos)
            tf.flush()
            tf.seek(0)
            return self.prepare_by_file(service_id, tf)

    def apply(self, task_id):
        endpoint = self.base_url + '/task/apply'
        return self.client.post(
            endpoint,
            data={'task_id': task_id},
        )

    def get_task_info(self, task_id):
        endpoint = self.base_url + '/task/info/%s' % task_id
        return self.client.get(endpoint)

    def revoke(self, task_id):
        endpoint = self.base_url + '/task/revoke/%s' % task_id
        return self.client.post(endpoint)

    def get_tasks(self, start=None, end=None):
        endpoint = self.base_url + '/tasks'
        params = {}
        if start is not None:
            params['start'] = date_str(start)
        if end is not None:
            params['end'] = date_str(end)
        return self.client.get(endpoint, params=params)

    def get_services(self):
        endpoint = self.base_url + '/services'
        return self.client.get(endpoint)


class ImageSetAPI(API):

    def __init__(self, client, image_set_id=None):
        super(ImageSetAPI, self).__init__(
            client, 'image_sets', '_0000014'
        )
        self.image_set_id = image_set_id

    def query(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def base_url(self):
        if self.image_set_id:
            return '%s/%s' % (
                super(ImageSetAPI, self).base_url,
                self.image_set_id
            )
        return super(ImageSetAPI, self).base_url

    def create_image_set(self, name, description=None):
        data = {'name': name}
        if description:
            data['description'] = description
        return self.client.post(self.base_url, json=data)

    def get_image_sets(self):
        return self.client.get(self.base_url)

    def add_images_in_bulk(self, img_infos):
        '''批量添加图片'''
        with _normalize_images_file(img_infos) as f:
            files = {'urls_to_add': f}
        return self.client.post(self.base_url, files=files)

    def delete_images_in_bulk(self, img_infos):
        with _normalize_images_file(img_infos) as f:
            files = {'urls_to_delete': f}
        return self.client.post(self.base_url, files=files)

    def add_image(self, image_url, meta=None, tags=''):
        form = {'image_url': image_url, 'meta': meta, 'tags': tags}
        return self.client.post(self.base_url, data=form)

    def delete_images(self, f_urls_to_delete):
        urls_to_delete = {'urls_to_delete': f_urls_to_delete}
        return self.client.post(self.base_url, files=urls_to_delete)

    def get_image_set(self):
        return self.client.get(self.base_url)

    def update_image_set(self, name=None, description=None):
        form = {}
        if name:
            form['name'] = name
        if description:
            form['description'] = description
        return self.client.put(self.base_url, data=form)

    def delete_image_set(self):
        return self.client.delete(self.base_url)

    def create_service(self, name, scenario):
        data = {'name': name, 'scenario': scenario}
        api_url = self.base_url + '/services'
        return self.client.post(api_url, json=data)


class CustomerServiceAPI(API):

    def __init__(self, client, service_id=None):
        super(CustomerServiceAPI, self).__init__(
            client, 'customer_services', '_0000172'
        )
        self.service_id = service_id

    def query(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def base_url(self):
        if self.service_id:
            return '%s/%s' % (
                super(CustomerServiceAPI, self).base_url,
                self.service_id
            )
        return super(CustomerServiceAPI, self).base_url

    def get_services(self):
        return self.client.get(self.base_url)

    def get_service(self):
        return self.client.get(self.base_url)

    def update_service(self, name):
        data = {'name': name}
        return self.client.put(self.base_url, json=data)

    def delete_service(self):
        return self.client.delete(self.base_url)


def make_auth_headers(access_key_id):
    headers = {
        'x-ca-accesskeyid': access_key_id,
        'x-ca-version': API_VERSION,
    }
    return headers


def get_default_session():
    s = requests.Session()
    # remount http and https adapters to config max_retries
    adapter = HTTPAdapter(
        max_retries=0,
        pool_connections=5,
        pool_maxsize=50,
        pool_block=True,
    )
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    return s


@contextmanager
def _normalize_images_file(x, tmpdir=None):
    if isinstance(x, six.string_types):
        with open(x) as f:
            yield f
    elif isinstance(x, list):
        with tempfile.NamedTemporaryFile(mode='w', dir=tmpdir) as tf:
            writer = csv.writer(tf)
            writer.writerows(x)
            tf.flush()
            with open(tf.name) as f:
                yield f
    else:
        yield x


def date_str(d):
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    if isinstance(d, six.string_types):
        dt.datetime.strptime(d, date_format)  # format check
        return d
    elif isinstance(d, (dt.date, dt.datetime)):
        return d.strftime(date_format)
    else:
        raise TypeError("Invalid date %r" % d)
