"""领域模块，按业务划分。

阶段 1 为空包。各模块在对应阶段创建，内部按需包含：
router.py / schemas.py / models.py / repository.py / service.py / permissions.py / exceptions.py

落地顺序：
    阶段 2 → auth / users / groups / knowledge_bases
    阶段 3 → documents / ingestion
    阶段 4-5 → retrieval
    阶段 6 → qa / assistant
"""
