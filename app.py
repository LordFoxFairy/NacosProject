import logging

from flask import Flask, render_template
from application.nacos_view import bp as nacos_view_bp

app = Flask(__name__)
app.register_blueprint(nacos_view_bp)

# 全局日志配置
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[
        logging.FileHandler("app.log"),  # 日志输出到文件
        logging.StreamHandler()  # 日志输出到控制台
    ]
)
# 创建一个全局的日志器实例
logger = logging.getLogger(__name__)


@app.route("/")
@app.route("/namespace")
def namespace():
    return render_template("namespace.html")


# 路由函数 - 命名空间详细信息页面
@app.route('/namespaces/<namespace_id>/details', methods=['GET'])
def namespace_details(namespace_id):
    return render_template('namespace_details.html', namespace_id=namespace_id)


if __name__ == '__main__':
    app.run(debug=True)
