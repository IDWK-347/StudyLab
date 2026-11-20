"""基础设施层：外部服务适配。

约束：被业务层调用，但**不得被业务层直接实例化**（README 第 4 节）。

阶段 1 只建 database/；elasticsearch / minio / redis / llm 分别在阶段 5 / 3 / 可选 / 4 落地。
（空目录不会被 git 跟踪，故不预先创建。）
"""
