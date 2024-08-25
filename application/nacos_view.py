import logging
from flask import Blueprint
from flask import jsonify, request

from application.decorators import api_doc
from application.nacos_client import NacosClient

bp = Blueprint('nacos', __name__, url_prefix="/api")
# 实例化 Nacos 客户端
nacos_client = NacosClient(server_address='http://192.168.1.110:8848', username='nacos', password='nacos')
logger = logging.getLogger(__name__)


@bp.route('/namespaces', methods=['GET'])
@api_doc(
    description="获取 Nacos 中所有的命名空间",
    tags="Nacos"
)
def list_namespaces():
    try:
        namespaces = nacos_client.get_namespaces()
        return jsonify(namespaces)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/namespaces/<namespace_id>/groups', methods=['GET'])
@api_doc(
    summary="获取指定命名空间下的所有组",
    tags="Nacos"
)
def list_groups(namespace_id):
    try:
        # 获取查询参数中的 pageNo 和 pageSize，如果未提供则使用默认值
        page_no = request.args.get('pageNo', default=1, type=int)
        page_size = request.args.get('pageSize', default=10, type=int)
        data_id = request.args.get('dataId', default='', type=str)
        group = request.args.get('group', default='', type=str)

        # 调用 Nacos 客户端方法获取组列表
        groups = nacos_client.get_groups(namespace_id, data_id, group, page_no=page_no, page_size=page_size)
        return jsonify(groups)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/namespaces/<namespace_id>/groups/<group>/data_ids', methods=['GET'])
@api_doc(
    summary="获取指定组下的所有数据ID",
    tags="Nacos"
)
def list_data_ids(namespace_id, group):
    try:
        # 获取查询参数中的 pageNo 和 pageSize，如果未提供则使用默认值
        page_no = request.args.get('pageNo', default=1, type=int)
        page_size = request.args.get('pageSize', default=10, type=int)
        search_data_id = request.args.get('dataId', default='', type=str)
        search_group = request.args.get('group', default='', type=str)

        # 获取模糊搜索关键字（可选）
        search_pattern = request.args.get('search', True, type=bool)

        if search_group != '':
            group = search_group

        # 调用 Nacos 客户端方法并传递分页参数和搜索关键字
        data_ids = nacos_client.get_data_ids(namespace_id, group, search_data_id, search_pattern, page_no=page_no, page_size=page_size)
        return jsonify(data_ids)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/namespaces/<namespace_id>/groups/<group>/data_ids/<data_id>', methods=['GET'])
@api_doc(
    summary="获取指定 data_id 的配置信息",
    tags="Nacos"
)
def get_config(namespace_id, group, data_id):
    try:
        # 调用 Nacos 客户端方法获取配置内容
        config_content = nacos_client.get_config(namespace_id, group, data_id)
        return jsonify(config_content)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# curl -X POST "http://localhost:5000/namespaces" -H "Content-Type: application/json" -d "{\"namespace_name\": \"new-namespace\", \"namespace_desc\": \"This is a new namespace\"}"
@bp.route('/namespaces', methods=['POST'])
@api_doc(
    summary="创建新的命名空间",
    tags="Nacos"
)
def create_namespace():
    try:
        # 从请求中获取命名空间的名称和描述
        namespace_name = request.json.get('namespace_name', '')
        namespace_desc = request.json.get('namespace_desc', '')

        # 调用 Nacos 客户端方法创建命名空间
        result = nacos_client.create_namespace(namespace_name, namespace_desc)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# curl -X POST "http://localhost:5000/api/namespaces/new-namespace/groups/DEFAULT_GROUP/data_ids/my-config" -H "Content-Type: application/json" -d "{\"content\": \"key1=value1\\nkey2=value2\", \"desc\": \"Test description\", \"type\": \"yaml\"}"
@bp.route('/namespaces/<namespace_id>/groups/<group>/data_ids/<data_id>', methods=['POST'])
@api_doc(
    summary="创建或更新指定 data_id 的配置信息，自动创建命名空间和组",
    tags="Nacos"
)
def create_or_update_full_config(namespace_id, group, data_id):
    try:
        # 从请求中获取配置信息和其他可选参数
        config_content = request.json.get('content', '')
        desc = request.json.get('desc', '')
        config_tags = request.json.get('config_tags', '')
        type_ = request.json.get('type', 'text')
        app_name = request.json.get('appName', '')

        # 获取现有命名空间列表
        namespaces = nacos_client.get_namespaces()
        existing_namespaces = [ns.get("namespaceShowName") for ns in namespaces.get("data", [])]

        # 如果命名空间不存在，先创建命名空间
        if namespace_id not in existing_namespaces:
            nacos_client.create_namespace(namespace_id)

        # 调用 Nacos API 发布配置
        result = nacos_client.publish_config(
            namespace_id=namespace_id,
            group=group,
            data_id=data_id,
            content=config_content,
            desc=desc,
            config_tags=config_tags,
            type_=type_,
            app_name=app_name
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
