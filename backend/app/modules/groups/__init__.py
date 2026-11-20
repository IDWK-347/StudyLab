"""群组模块。

范围：`groups` / `group_members` / `group_invitations` / `group_join_requests` 四张表，
群组 CRUD、成员与群组角色、定向邀请、加入申请、解散。

不包含：知识库与归档（表未设计，见 v1.1项目文档.md 第 3 节）、系统级用户管理——那些在
modules/users。
"""
