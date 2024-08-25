import hashlib
import json
import logging
import threading
import time

import requests

# 创建一个全局的日志器实例
logger = logging.getLogger(__name__)


class NacosClient:
    def __init__(self, server_address, username=None, password=None):
        self.server_address = server_address
        self.auth = (username, password) if username and password else None
        self.listeners = {}  # 保存监听器，key 为 (namespace_id, group, data_id)
        self.observers = {}  # 观察者模式的存储

    def create_namespace(self, namespace_name, namespace_desc=""):
        url = f"{self.server_address}/nacos/v1/console/namespaces"
        params = {
            'customNamespaceId': namespace_name,
            'namespaceName': namespace_name,
            'namespaceDesc': namespace_desc
        }
        response = requests.post(url, params=params, auth=self.auth)
        if response.status_code == 200:
            return {"message": "Namespace created successfully"}
        else:
            raise Exception(f"Failed to create namespace {namespace_name}: {response.text}")

    def publish_config(self, namespace_id, group, data_id, content, desc='', config_tags='', type_='text', app_name=''):
        url = f"{self.server_address}/nacos/v1/cs/configs"
        params = {
            'dataId': data_id,
            'group': group,
            'tenant': namespace_id,
            'namespaceId': namespace_id,
            'type': type_,
            'desc': desc,
            'config_tags': config_tags,
            'appName': app_name
        }
        data = {
            'content': content
        }

        response = requests.post(url, params=params, data=data, auth=self.auth)
        if response.status_code == 200 and response.text == "true":

            # 注册观察者并添加监听
            self.add_listener(namespace_id, group, data_id, self.on_config_update)

            return {"message": "Configuration published successfully"}
        else:
            raise Exception(
                f"Failed to publish configuration for dataId {data_id} in group {group}, namespace {namespace_id}: {response.text}")

    @staticmethod
    def on_config_update(namespace_id, group, data_id, new_content):
        logger.info(f"Config updated for {namespace_id} - {group} - {data_id}: {new_content}")

    def get_namespaces(self):
        url = f"{self.server_address}/nacos/v1/console/namespaces"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to retrieve namespaces: {response.text}")

    def get_groups(self, namespace_id, data_id, group, page_no=1, page_size=10):
        url = f"{self.server_address}/nacos/v1/cs/configs"
        params = {
            'search': 'accurate',
            'pageNo': page_no,
            'pageSize': page_size,
            'namespaceId': namespace_id,
            'tenant': namespace_id,
            'dataId': data_id,  # 尝试使用空字符串作为通配符
            'group': group,  # 尝试使用空字符串作为通配符
        }

        logger.info(f"{params}")

        all_groups = set()
        while True:
            response = requests.get(url, params=params, auth=self.auth)
            logger.info(f"{response.headers}")

            if response.status_code == 200:
                data = response.json()
                current_groups = set(item['group'] for item in data.get('pageItems', []))
                all_groups.update(current_groups)

                if data.get('pageNumber') < data.get('pagesAvailable'):
                    params['pageNo'] += 1
                else:
                    break
            else:
                raise Exception(f"Failed to retrieve groups for namespace {namespace_id}: {response.text}")

        return list(all_groups)

    def get_data_ids(self, namespace_id, group, search_data_id='', search_pattern=None, page_no=1, page_size=10):
        url = f"{self.server_address}/nacos/v1/cs/configs"
        params = {
            'search': 'blur' if search_pattern else 'accurate',  # 模糊搜索或精确搜索
            'dataId': f"*{search_data_id}*" if search_pattern else search_data_id,  # 搜索的 dataId（如果指定）
            'group': group,  # 指定的组
            'tenant': namespace_id,  # 指定的命名空间（tenant）
            'pageNo': page_no,  # 页码
            'pageSize': page_size  # 每页数量
        }

        logger.info(f"Request Params: {params}")

        response = requests.get(url, params=params, auth=self.auth)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response Data: {data}")
            return data
        else:
            raise Exception(
                f"Failed to retrieve data IDs for group {group} in namespace {namespace_id}: {response.text}")

    def get_config(self, namespace_id, group, data_id):
        url = f"{self.server_address}/nacos/v1/cs/configs"
        params = {
            'dataId': data_id,  # 指定的 dataId
            'group': group,  # 指定的组
            'tenant': namespace_id,  # 使用 'namespaceId' 指定命名空间
            'show': 'all'  # 确保返回所有配置信息
        }

        # 调试信息：打印请求的 URL 和参数
        logger.info(f"Requesting config with URL: {url}")
        logger.info(f"Request parameters: {params}")

        response = requests.get(url, params=params, auth=self.auth)

        # 调试信息：打印响应状态码和内容
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")

        if response.status_code == 200:
            if len(response.text.strip(' ')) == 0:
                return response.text
            return response.json()  # 配置信息通常是纯文本
        else:
            raise Exception(
                f"Failed to retrieve configuration for dataId {data_id} in group {group}, namespace {namespace_id}: {response.text}")

    def add_listener(self, namespace_id, group, data_id, callback):
        """
        添加监听器，当指定的配置发生变动时，调用回调函数。
        该方法同时处理注册观察者和监听的功能。
        """
        key = (namespace_id, group, data_id)
        if key not in self.listeners:
            self.listeners[key] = {
                'callback': callback,
                'last_md5': None  # 存储最新的配置MD5
            }
            threading.Thread(target=self._listener_thread, args=(namespace_id, group, data_id)).start()

    def _listener_thread(self, namespace_id, group, data_id):
        key = (namespace_id, group, data_id)
        while True:
            try:
                current_config = self.get_config(namespace_id, group, data_id)
                current_md5 = self._calculate_md5(current_config)
                # current_md5 = dict(current_config).get('md5')
                print(f"[DEBUG] Current MD5: {current_md5}, Last MD5: {self.listeners[key]['last_md5']}")

                if self.listeners[key]['last_md5'] is None:
                    self.listeners[key]['last_md5'] = current_md5

                if self.listeners[key]['last_md5'] != current_md5:
                    print(f"[DEBUG] Detected change in config for {namespace_id} - {group} - {data_id}")
                    self.listeners[key]['last_md5'] = current_md5
                    self.listeners[key]['callback'](namespace_id, group, data_id, current_config)  # 传递必要的参数

                time.sleep(30)  # 定期检查配置是否有变动，间隔30秒
            except Exception as e:
                print(f"Error listening to changes: {e}")
                time.sleep(30)  # 在错误时重试

    @staticmethod
    def _calculate_md5(content):
        """
        计算配置内容的MD5值。内容应为字典类型。
        """
        content_str = json.dumps(content, sort_keys=True)  # 将字典转为字符串
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()