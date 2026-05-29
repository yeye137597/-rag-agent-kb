import gc
import json
from pathlib import Path

import streamlit as st

from config import KNOWLEDGE_BASE_ROOT, LOG_FILE, TOP_K
from src.agent_graph import ask_question
from src.auth import (
    authenticate_user,
    create_user,
    get_authorized_kb_ids,
    get_user_permissions,
    initialize_auth,
    list_audit_logs,
    list_users,
    register_user,
    replace_user_read_permissions,
    reset_user_password,
    set_user_active,
    write_audit_log,
)
from src.document_loader import load_documents
from src.kb_manager import (
    KnowledgeBaseInUseError,
    create_knowledge_base,
    delete_knowledge_base,
    get_kb_paths,
    list_knowledge_bases,
    update_kb_metadata,
)
from src.llm import has_deepseek_api_key
from src.retriever import build_multi_kb_retriever
from src.splitter import split_documents
from src.utils import clean_text, ensure_directories, format_doc_source, save_cleaned_text, save_uploaded_file
from src.vector_store import build_vector_store


def extract_plain_text(file_path: Path) -> str:
    documents, errors = load_documents([file_path])
    if errors:
        raise RuntimeError("; ".join(errors))
    return "\n\n".join(doc.page_content for doc in documents)


def add_kb_metadata(chunks, kb_id: str, kb_name: str):
    for chunk in chunks:
        chunk.metadata = chunk.metadata or {}
        chunk.metadata["kb_id"] = kb_id
        chunk.metadata["kb_name"] = kb_name
    return chunks


def build_kb_lookup():
    knowledge_bases = list_knowledge_bases()
    return knowledge_bases, {kb["id"]: kb for kb in knowledge_bases}


def release_kb_runtime_state(kb_id: str) -> None:
    st.session_state.chunks_by_kb.pop(kb_id, None)
    if st.session_state.get("clean_kb_id") == kb_id:
        st.session_state.uploaded_paths = []
        st.session_state.cleaned_paths = []
        st.session_state.clean_preview = []
        st.session_state.use_cleaned_files = False
        st.session_state.clean_kb_id = ""

    for key in ("vector_store", "retriever", "current_kb", "selected_kbs", "cached_chroma", "chroma", "current_retriever"):
        st.session_state.pop(key, None)

    if "selected_query_kb_ids" in st.session_state:
        st.session_state.selected_query_kb_ids = [
            item for item in st.session_state.selected_query_kb_ids if item != kb_id
        ]

    st.cache_resource.clear()
    st.cache_data.clear()
    gc.collect()


def init_session_state() -> None:
    defaults = {
        "logged_in": False,
        "username": "",
        "role": "",
        "user_id": None,
        "chunks_by_kb": {},
        "uploaded_paths": [],
        "cleaned_paths": [],
        "clean_preview": [],
        "use_cleaned_files": False,
        "clean_kb_id": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_login_page() -> None:
    st.title("智能知识库问答系统")
    st.info("首次登录后请尽快修改默认管理员密码。")
    login_tab, register_tab = st.tabs(["登录", "注册账号"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录", type="primary")

        if submitted:
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user["username"]
                st.session_state.role = user["role"]
                st.session_state.user_id = user["user_id"]
                write_audit_log(user["username"], "用户登录成功", "用户登录系统")
                st.rerun()
            else:
                write_audit_log(username.strip(), "登录失败", "用户名或密码错误")
                st.error("用户名或密码错误。")

    with register_tab:
        with st.form("register_form"):
            reg_username = st.text_input("用户名", key="register_username")
            reg_password = st.text_input("密码", type="password", key="register_password")
            confirm_password = st.text_input("确认密码", type="password", key="register_confirm_password")
            register_submitted = st.form_submit_button("注册")

        if register_submitted:
            if reg_password != confirm_password:
                st.error("两次输入的密码不一致。")
            else:
                ok, message = register_user(reg_username, reg_password)
                if ok:
                    st.success(message)
                else:
                    st.error(message)


def logout() -> None:
    write_audit_log(st.session_state.username, "用户退出登录", "用户退出系统")
    for key in ("logged_in", "username", "role", "user_id"):
        st.session_state[key] = False if key == "logged_in" else ""
    st.session_state.user_id = None
    st.rerun()


def can_write_kb(kb_id: str) -> bool:
    if st.session_state.role == "admin":
        return True
    return kb_id in get_authorized_kb_ids(st.session_state.user_id, write_required=True)


def get_visible_kbs(all_kbs: list[dict]) -> list[dict]:
    if st.session_state.role == "admin":
        return all_kbs
    allowed_ids = get_authorized_kb_ids(st.session_state.user_id, write_required=False)
    return [kb for kb in all_kbs if kb["id"] in allowed_ids]


def read_query_logs(username: str | None = None, limit: int = 50) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    rows = []
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if username is None or item.get("username") == username:
                rows.append(item)
    return rows[-limit:][::-1]


def role_label(role: str) -> str:
    return "管理员" if role == "admin" else "普通用户"


def show_user_management(knowledge_bases: list[dict], kb_by_id: dict) -> None:
    st.header("用户管理")

    with st.expander("创建用户", expanded=False):
        with st.form("create_user_form"):
            username = st.text_input("用户名", key="new_user_username")
            password = st.text_input("密码", type="password", key="new_user_password")
            role = st.selectbox("角色", ["user", "admin"], key="new_user_role")
            submitted = st.form_submit_button("创建用户")
        if submitted:
            try:
                create_user(username, password, role)
                write_audit_log(st.session_state.username, "管理员创建用户", f"username={username}, role={role}")
                st.success("用户已创建。")
                st.rerun()
            except Exception as exc:
                st.error(f"创建用户失败：{exc}")

    users = list_users()
    st.subheader("用户列表")

    header_cols = st.columns([1.2, 1, 0.8, 1.6, 2.4, 1])
    header_cols[0].markdown("**用户名**")
    header_cols[1].markdown("**角色**")
    header_cols[2].markdown("**状态**")
    header_cols[3].markdown("**创建时间**")
    header_cols[4].markdown("**可访问知识库**")
    header_cols[5].markdown("**保存授权**")

    kb_options = [kb["id"] for kb in knowledge_bases]
    for user in users:
        row_cols = st.columns([1.2, 1, 0.8, 1.6, 2.4, 1])
        row_cols[0].write(user["username"])
        row_cols[1].write(role_label(user["role"]))
        row_cols[2].write("启用" if user["is_active"] else "禁用")
        row_cols[3].write(user["created_at"])

        if user["role"] == "admin":
            row_cols[4].write("管理员默认可访问全部知识库")
            row_cols[5].write("-")
        else:
            current_read_kbs = [
                perm["kb_id"]
                for perm in get_user_permissions(user["id"])
                if perm.get("can_read") and perm["kb_id"] in kb_by_id
            ]
            selected_kb_ids = row_cols[4].multiselect(
                "可访问知识库",
                options=kb_options,
                default=current_read_kbs,
                format_func=lambda kb_id: kb_by_id[kb_id]["name"],
                key=f"user_kb_access_{user['id']}",
                label_visibility="collapsed",
            )
            if row_cols[5].button("保存授权", key=f"save_user_kb_access_{user['id']}"):
                replace_user_read_permissions(user["id"], selected_kb_ids)
                write_audit_log(
                    st.session_state.username,
                    "管理员授权知识库",
                    f"user={user['username']}, kb_ids={selected_kb_ids}, can_read=1, can_write=0",
                )
                st.success(f"已更新用户 {user['username']} 的知识库访问权限。")
                st.rerun()

    if users:
        user_options = {f"{u['username']} ({u['role']}, id={u['id']})": u for u in users}
        selected_label = st.selectbox("选择用户", list(user_options.keys()))
        selected_user = user_options[selected_label]

        col1, col2 = st.columns(2)
        with col1:
            if selected_user["is_active"]:
                if st.button("禁用用户", use_container_width=True):
                    set_user_active(selected_user["id"], False)
                    write_audit_log(st.session_state.username, "管理员禁用用户", selected_user["username"])
                    st.success("用户已禁用。")
                    st.rerun()
            else:
                if st.button("启用用户", use_container_width=True):
                    set_user_active(selected_user["id"], True)
                    write_audit_log(st.session_state.username, "管理员启用用户", selected_user["username"])
                    st.success("用户已启用。")
                    st.rerun()

        with col2:
            new_password = st.text_input("重置密码", type="password", key="reset_password")
            if st.button("修改密码", use_container_width=True):
                try:
                    reset_user_password(selected_user["id"], new_password)
                    write_audit_log(st.session_state.username, "管理员修改密码", selected_user["username"])
                    st.success("密码已修改。")
                except Exception as exc:
                    st.error(f"修改密码失败：{exc}")



st.set_page_config(page_title="智能知识库问答系统", page_icon="📚", layout="wide")
ensure_directories()
initialize_auth()
init_session_state()

if not st.session_state.logged_in:
    show_login_page()
    st.stop()

st.title("智能知识库问答系统")

with st.sidebar:
    st.write(f"当前用户：{st.session_state.username}")
    st.write(f"角色：{role_label(st.session_state.role)}")
    if st.button("退出登录", use_container_width=True):
        logout()

knowledge_bases, kb_by_id = build_kb_lookup()
visible_kbs = get_visible_kbs(knowledge_bases)
visible_kb_by_id = {kb["id"]: kb for kb in visible_kbs}
visible_kb_ids = [kb["id"] for kb in visible_kbs]

with st.sidebar:
    if st.session_state.role == "admin":
        st.header("知识库管理")
        new_kb_name = st.text_input("新知识库名称", placeholder="例如：RAG学习知识库")
        if st.button("创建知识库", use_container_width=True):
            try:
                created = create_knowledge_base(new_kb_name)
                write_audit_log(st.session_state.username, "创建知识库", f"{created['name']} ({created['id']})")
                st.success(f"已创建知识库：{created['name']}")
                st.rerun()
            except Exception as exc:
                st.error(f"创建失败：{exc}")

    writable_kbs = knowledge_bases if st.session_state.role == "admin" else [
        kb for kb in visible_kbs if can_write_kb(kb["id"])
    ]
    writable_kb_by_id = {kb["id"]: kb for kb in writable_kbs}
    writable_kb_ids = [kb["id"] for kb in writable_kbs]

    if writable_kbs:
        st.divider()
        if st.session_state.role == "admin":
            st.header("文件处理与构建")
        else:
            st.header("我可维护的知识库")
        selected_build_kb_id = st.selectbox(
            "构建知识库时使用",
            options=writable_kb_ids,
            format_func=lambda kb_id: f"{writable_kb_by_id[kb_id]['name']} ({kb_id})",
        )
        uploaded_files = st.file_uploader(
            "上传学习资料、课程资料或项目文档",
            type=["pdf", "docx", "md", "txt"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            st.caption(f"已选择 {len(uploaded_files)} 个文件")

        if st.button("清洗文件", use_container_width=True):
            if not uploaded_files:
                st.warning("请先上传文件。")
            else:
                kb = writable_kb_by_id[selected_build_kb_id]
                paths = get_kb_paths(selected_build_kb_id)
                saved_paths = [save_uploaded_file(uploaded_file, paths["uploads"]) for uploaded_file in uploaded_files]
                write_audit_log(st.session_state.username, "上传文件", f"kb_id={selected_build_kb_id}, files={len(saved_paths)}")
                preview_items = []
                cleaned_paths = []

                with st.spinner("正在解析并清洗文件..."):
                    for file_path in saved_paths:
                        try:
                            original_text = extract_plain_text(file_path)
                            cleaned_text = clean_text(original_text)
                            cleaned_path = save_cleaned_text(file_path, cleaned_text, paths["processed"])
                            cleaned_paths.append(cleaned_path)
                            preview_items.append(
                                {
                                    "filename": file_path.name,
                                    "kb_id": kb["id"],
                                    "kb_name": kb["name"],
                                    "original_chars": len(original_text),
                                    "cleaned_chars": len(cleaned_text),
                                    "original_preview": original_text[:500],
                                    "cleaned_preview": cleaned_text[:500],
                                    "cleaned_path": cleaned_path,
                                    "error": "",
                                }
                            )
                        except Exception as exc:
                            preview_items.append(
                                {
                                    "filename": file_path.name,
                                    "kb_id": kb["id"],
                                    "kb_name": kb["name"],
                                    "original_chars": 0,
                                    "cleaned_chars": 0,
                                    "original_preview": "",
                                    "cleaned_preview": "",
                                    "cleaned_path": None,
                                    "error": str(exc),
                                }
                            )

                st.session_state.uploaded_paths = saved_paths
                st.session_state.cleaned_paths = cleaned_paths
                st.session_state.clean_preview = preview_items
                st.session_state.use_cleaned_files = False
                st.session_state.clean_kb_id = selected_build_kb_id
                write_audit_log(st.session_state.username, "清洗文件", f"kb_id={selected_build_kb_id}, cleaned={len(cleaned_paths)}")
                st.success(f"清洗完成，已生成 {len(cleaned_paths)} 个清洗文件。")

        if st.button("确认使用清洗后的文件构建知识库", use_container_width=True):
            if not st.session_state.cleaned_paths:
                st.warning("请先点击“清洗文件”。")
            elif selected_build_kb_id != st.session_state.clean_kb_id:
                st.warning("当前选择的知识库和清洗文件所属知识库不一致，请重新清洗。")
            else:
                st.session_state.use_cleaned_files = True
                st.success("已确认：构建知识库时将使用清洗后的文件。")

        if st.button("构建知识库", type="primary", use_container_width=True):
            if not uploaded_files and not st.session_state.uploaded_paths:
                st.warning("请先上传文档并构建知识库。")
            else:
                kb = writable_kb_by_id[selected_build_kb_id]
                paths = get_kb_paths(selected_build_kb_id)
                if (
                    st.session_state.use_cleaned_files
                    and st.session_state.cleaned_paths
                    and st.session_state.clean_kb_id == selected_build_kb_id
                ):
                    build_paths = st.session_state.cleaned_paths
                    source_label = "清洗后的文件"
                else:
                    if uploaded_files:
                        build_paths = [save_uploaded_file(uploaded_file, paths["uploads"]) for uploaded_file in uploaded_files]
                        st.session_state.uploaded_paths = build_paths
                    else:
                        build_paths = st.session_state.uploaded_paths
                    source_label = "原始文件"

                with st.spinner(f"正在使用{source_label}解析、切片并写入当前知识库..."):
                    documents, errors = load_documents(build_paths)
                    chunks = add_kb_metadata(split_documents(documents), kb_id=kb["id"], kb_name=kb["name"])
                    build_vector_store(chunks, paths["chroma_db"])
                    st.session_state.chunks_by_kb[kb["id"]] = chunks
                    update_kb_metadata(kb["id"], file_count=len(build_paths), chunk_count=len(chunks))

                if errors:
                    st.error("部分文档解析失败：")
                    for error in errors:
                        st.write(f"- {error}")
                if chunks:
                    write_audit_log(st.session_state.username, "用户构建知识库", f"kb_id={kb['id']}, chunks={len(chunks)}")
                    st.success(f"知识库构建完成，共写入 {len(chunks)} 个片段。")
                    st.rerun()
                else:
                    st.warning("没有成功解析出可写入知识库的内容。")

    if st.session_state.role == "admin":
        st.divider()
        st.header("删除知识库")
        if knowledge_bases:
            delete_kb_id = st.selectbox(
                "选择要删除的知识库",
                options=[kb["id"] for kb in knowledge_bases],
                format_func=lambda kb_id: f"{kb_by_id[kb_id]['name']} ({kb_id})",
                key="delete_kb_select",
            )
            confirm_delete = st.checkbox("我确认删除该知识库")
            if st.button("删除知识库", use_container_width=True):
                if not confirm_delete:
                    st.warning("请先勾选确认删除。")
                else:
                    try:
                        release_kb_runtime_state(delete_kb_id)
                        delete_knowledge_base(delete_kb_id)
                        write_audit_log(st.session_state.username, "删除知识库", delete_kb_id)
                        st.success("知识库已删除。")
                        st.rerun()
                    except KnowledgeBaseInUseError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"删除失败：{exc}")

    st.divider()
    st.write("当前配置")
    st.write(f"- Top K: {TOP_K}")
    st.write(f"- 知识库根目录: `{KNOWLEDGE_BASE_ROOT}`")

if st.session_state.role == "admin":
    tab_kb, tab_qa, tab_users, tab_logs = st.tabs(["知识库管理", "知识库问答", "用户管理", "日志/审计"])
else:
    tab_qa, tab_logs = st.tabs(["知识库问答", "我的问答日志"])
    tab_kb = None
    tab_users = None

if tab_kb is not None:
    with tab_kb:
        st.subheader("已有知识库")
        if not knowledge_bases:
            st.info("暂无知识库。")
        else:
            cols = st.columns(min(4, len(knowledge_bases)))
            for index, kb in enumerate(knowledge_bases):
                metadata = kb.get("metadata", {})
                with cols[index % len(cols)]:
                    st.metric(kb["name"], f"{metadata.get('chunk_count', 0)} chunks")
                    st.caption(f"ID: `{kb['id']}`")
                    st.caption(f"文件数: {metadata.get('file_count', 0)}")

        if st.session_state.clean_preview:
            st.subheader("清洗预览")
            for item in st.session_state.clean_preview:
                with st.expander(f"{item['kb_name']} / {item['filename']} 清洗前后对比", expanded=True):
                    if item["error"]:
                        st.error(f"清洗失败：{item['error']}")
                        continue
                    col1, col2 = st.columns(2)
                    col1.metric("原始字符数", item["original_chars"])
                    col2.metric("清洗后字符数", item["cleaned_chars"])
                    before, after = st.columns(2)
                    with before:
                        st.caption("清洗前前 500 字")
                        st.text_area("原文预览", value=item["original_preview"], height=220, disabled=True)
                    with after:
                        st.caption("清洗后前 500 字")
                        st.text_area("清洗预览", value=item["cleaned_preview"], height=220, disabled=True)
                    st.caption(f"清洗文件：`{item['cleaned_path']}`")

with tab_qa:
    st.subheader("知识库问答")
    if st.session_state.role == "user" and not visible_kbs:
        st.warning("当前账号暂未授权任何知识库，请联系管理员。")
    selected_query_kb_ids = st.multiselect(
        "选择用于检索的知识库",
        options=visible_kb_ids,
        default=visible_kb_ids[:1],
        format_func=lambda kb_id: f"{visible_kb_by_id[kb_id]['name']} ({kb_id})",
        key="selected_query_kb_ids",
    )
    selected_query_kbs = [
        {"id": kb_id, "name": visible_kb_by_id[kb_id]["name"], "paths": get_kb_paths(kb_id)}
        for kb_id in selected_query_kb_ids
        if kb_id in visible_kb_by_id
    ]

    if selected_query_kbs:
        st.caption("当前选择的知识库：" + "、".join(kb["name"] for kb in selected_query_kbs))

    question = st.text_area("请输入你的问题", height=110, placeholder="例如：这个项目的核心功能有哪些？")
    ask = st.button("生成答案", type="primary")

    if ask:
        if not question.strip():
            st.warning("请输入问题。")
        elif not selected_query_kbs:
            st.warning("请至少选择一个已授权知识库。")
        elif not has_deepseek_api_key():
            st.error("未配置 DEEPSEEK_API_KEY。请复制 .env.example 为 .env，并填写 DeepSeek API Key。")
        else:
            with st.spinner("正在检索知识库并生成答案..."):
                try:
                    retriever = build_multi_kb_retriever(
                        selected_query_kbs,
                        current_chunks_by_kb=st.session_state.chunks_by_kb,
                        top_k=TOP_K,
                    )
                    write_audit_log(
                        st.session_state.username,
                        "发起问答",
                        f"kbs={[kb['id'] for kb in selected_query_kbs]}, question={question[:80]}",
                    )
                    result = ask_question(
                        question.strip(),
                        retriever,
                        selected_kbs=selected_query_kbs,
                        username=st.session_state.username,
                        role=st.session_state.role,
                    )
                except Exception as exc:
                    st.error(f"问答失败：{exc}")
                    st.stop()

            st.subheader("答案")
            st.markdown(result.get("answer", "当前知识库中没有找到足够信息。"))

            col1, col2, col3 = st.columns(3)
            col1.metric("重试次数", result.get("retry_count", 0))
            col2.metric("耗时", f"{result.get('latency', 0)}s")
            col3.metric("是否足够", "是" if result.get("is_enough") else "否")

            if result.get("rewritten_question") and result.get("rewritten_question") != question.strip():
                st.info(f"改写后的查询词：{result.get('rewritten_question')}")
            if result.get("evaluation_reason"):
                st.caption(f"检索评估：{result.get('evaluation_reason')}")

            st.subheader("检索来源片段")
            docs = result.get("docs", [])
            if not docs:
                st.warning("没有检索到内容，当前知识库信息不足。")
            for index, doc in enumerate(docs, start=1):
                metadata = doc.metadata or {}
                kb_name = metadata.get("kb_name", "N/A")
                source = metadata.get("source", "N/A")
                page = metadata.get("page", "N/A") or "N/A"
                chunk_id = metadata.get("chunk_id", "N/A")
                title = f"片段 {index} | 知识库: {kb_name} | 来源: {source} | 页码: {page} | chunk_id: {chunk_id}"
                with st.expander(title, expanded=index == 1):
                    st.write(doc.page_content)
                    st.caption(format_doc_source(doc))
                    st.json(metadata)

if tab_users is not None:
    with tab_users:
        show_user_management(knowledge_bases, kb_by_id)

with tab_logs:
    if st.session_state.role == "admin":
        audit_tab, query_tab = st.tabs(["审计日志", "问答日志"])
        with audit_tab:
            st.subheader("最近审计日志")
            audit_logs = list_audit_logs(limit=100)
            if not audit_logs:
                st.info("暂无审计日志。")
            else:
                st.dataframe(audit_logs, use_container_width=True, hide_index=True)

        with query_tab:
            st.subheader("全部问答日志")
            logs = read_query_logs(username=None, limit=100)
            if not logs:
                st.info("暂无问答日志。")
            else:
                for item in logs:
                    username = item.get("username", "")
                    question_preview = item.get("question", "")[:60]
                    with st.expander(f"{item.get('time', '')} | {username} | {question_preview}"):
                        st.write("用户：", username)
                        st.write("角色：", role_label(item.get("role", "")))
                        st.write("问题：", item.get("question", ""))
                        st.write("答案：", item.get("answer", ""))
                        st.json(
                            {
                                "selected_kbs": item.get("selected_kbs", []),
                                "latency": item.get("latency"),
                                "retry_count": item.get("retry_count"),
                                "evaluation_reason": item.get("evaluation_reason"),
                            }
                        )
    else:
        st.subheader("我的问答记录")
        logs = read_query_logs(username=st.session_state.username)
        if not logs:
            st.info("暂无问答记录。")
        else:
            for item in logs:
                with st.expander(f"{item.get('time', '')} | {item.get('question', '')[:60]}"):
                    st.write("问题：", item.get("question", ""))
                    st.write("答案：", item.get("answer", ""))
                    st.json(
                        {
                            "selected_kbs": item.get("selected_kbs", []),
                            "latency": item.get("latency"),
                            "retry_count": item.get("retry_count"),
                            "evaluation_reason": item.get("evaluation_reason"),
                        }
                    )
