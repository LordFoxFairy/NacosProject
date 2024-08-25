from functools import wraps


def api_doc(summary=None, description="无", tags="无", parameters=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # 如果 summary 为空，则使用函数名称
        doc_summary = summary if summary is not None else func.__name__

        # 生成 parameters 部分
        params_doc = ""
        if parameters:
            params_doc = f"""
            parameters:
            {parameters}
            """

        wrapper.__doc__ = f"""
        {doc_summary}
        ---
        tags:
          - {tags}
        description: {description}
        {params_doc}
        responses:
          200:
            description: 成功返回
        """
        return wrapper

    return decorator
