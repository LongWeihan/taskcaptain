#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path('/home/a/.openclaw/workspace-local8317/products-ui')
DATA = ROOT / 'data'
PRODUCTS = DATA / 'products'
TRASH = DATA / 'trash'
CLAW_PROFILES = DATA / 'claw-profiles'
RUNS = ROOT / 'runs'
ACPX = Path('/home/a/.openclaw/extensions/acpx/node_modules/.bin/acpx')

HOST = '127.0.0.1'
PORT = 8765
DEFAULT_LANG = 'en'
DEFAULT_PROFILE_ID = 'sandrone-default'

for p in [PRODUCTS, TRASH, CLAW_PROFILES, RUNS]:
    p.mkdir(parents=True, exist_ok=True)

ACTIVE_RUNS: dict[str, dict] = {}
RUN_LOCK = threading.Lock()

I18N = {
    'zh': {
        'app_title': 'TaskCaptain 产品控制台',
        'app_subtitle': '本地产品工作台：把 User↔Agent、Agent↔Codex、日志拆开，同时保持可复用的独立身份。',
        'language': '语言',
        'lang_zh': '中文',
        'lang_en': 'English',
        'create_product': '创建新任务',
        'product_name': '任务名称',
        'goal': '目标',
        'goal_placeholder': '这个任务要实现什么？',
        'product_folder': '工作目录（可写范围）',
        'claw_endpoint': 'Agent 端点',
        'claw_api_key': 'Agent API Key',
        'claw_model': 'Agent 模型（留空则继承 profile）',
        'claw_thinking': 'Agent 思考强度（留空则继承 profile）',
        'claw_profile': 'Agent Profile',
        'claw_profile_select': '选择可复用的 Agent Profile',
        'claw_soul': 'Agent Soul（留空则继承 profile）',
        'claw_skills': 'Agent Skills（留空则继承 profile）',
        'codex_endpoint': 'Codex 端点',
        'codex_api_key': 'Codex API Key',
        'codex_model': 'Codex 模型',
        'codex_thinking': 'Codex 思考强度',
        'enable_plan': '启用 Codex Plan 模式（尽力设置）',
        'enable_max_permission': 'Codex 最高权限（工作目录内 approve-all）',
        'create_button': '创建任务',
        'active_products': '现有任务',
        'no_products': '还没有任务，先在右侧创建一个。',
        'created_at': '创建时间',
        'back': '← 返回控制台',
        'status': '状态',
        'self_test': '自检',
        'configuration_details': '配置详情',
        'workspace_folder': '工作目录',
        'claw_setting': 'Agent 设置',
        'codex_setting': 'Codex 设置',
        'model': '模型',
        'thinking': '思考',
        'modes': '模式',
        'api_key_present': 'API Key 已设置',
        'yes': '是',
        'no': '否',
        'run_self_test': '运行自检',
        'start_continue_run': '开始 / 继续运行',
        'stop_run': '停止运行',
        'delete_product': '删除任务',
        'delete_confirm': '确定删除这个任务吗？会移动到回收区。',
        'bulk_delete': '批量删除选中项目',
        'bulk_delete_confirm': '确定批量删除选中的项目吗？运行中的项目会跳过，其他会移动到回收区。',
        'select_for_bulk_delete': '全选用于批量删除',
        'running_skip_note': '运行中的项目不会被批量删除',
        'append_requirement': '发送给 Agent',
        'append_placeholder': '给 Agent 的新需求、修正意见、交付约束……',
        'append_button': '发送',
        'user_claw_dialogue': 'User ↔ Agent 对话区',
        'claw_codex_dialogue': 'Agent ↔ Codex 对话区',
        'no_user_claw': '还没有 User ↔ Agent 对话。',
        'no_claw_codex': '还没有 Agent ↔ Codex 对话。',
        'claw_log': 'Agent 日志',
        'codex_log': 'Codex 日志',
        'no_logs': '还没有日志。',
        'untitled': '未命名任务',
        'self_test_details': '自检详情',
        'not_run': '未运行',
        'idle': '空闲',
        'running': '运行中',
        'stopped': '已停止',
        'delivered': '已交付',
        'failed': '失败',
        'passed': '通过',
        'check': '检查项',
        'result': '结果',
        'detail': '详情',
        'role_policy_title': '执行分工策略',
        'role_policy_body': '当前产品策略：主要代码和产品文件由 Codex 在产品目录内完成；Agent 负责规划、监督、联网、下载数据集、归纳需求与状态推进，不直接在产品目录内写主产品代码。',
        'claw_identity_title': 'Agent 独立身份',
        'claw_identity_body': 'Agent 现在被建模成可复用 profile：profile 负责默认 soul / skills / model / thinking；每个产品只是在此基础上做局部覆盖，因此不会和 Codex 绑成同一个东西。',
        'effective_claw_identity': '当前生效的 Agent 身份',
        'profile_name': 'Profile 名称',
        'profile_description': 'Profile 描述',
        'profile_soul_placeholder': '例如：Rigorous, efficient, pragmatic supervisor. Think like an engineer-scientist.',
        'profile_skills_placeholder': '例如：complex planning\nnetwork / computer / AI debugging\nautonomous exploration',
        'profile_desc_placeholder': '这个 Agent profile 适合什么项目、有什么风格？',
        'reusable_claw_profiles': '可复用 Agent Profiles',
        'no_profiles': '还没有 profile，将自动使用默认的 Sandrone profile。',
        'create_profile': '创建新 Profile',
        'create_profile_button': '创建 Profile',
        'save_current_claw_profile': '把当前 Agent 保存成可复用 Profile',
        'save_profile_button': '保存为 Profile',
        'profile_saved_hint': '保存后，新项目可直接复用这个 Agent。',
        'profile_label': 'Profile',
        'soul_label': 'Soul',
        'skills_label': 'Skills',
        'inherited_from_profile': '继承自 profile',
        'profile_model_hint': 'Profile 默认模型',
        'profile_thinking_hint': 'Profile 默认思考强度',
    },
    'en': {
        'app_title': 'TaskCaptain Console',
        'app_subtitle': 'Local task workspace: Separate User↔Agent and Agent↔Codex dialogues and logs, with reusable independent profiles.',
        'language': 'Language',
        'lang_zh': '中文',
        'lang_en': 'English',
        'create_product': 'Create New Task',
        'product_name': 'Task Name',
        'goal': 'Goal',
        'goal_placeholder': 'What should this task achieve?',
        'product_folder': 'Workspace Folder (Codex writable)',
        'claw_endpoint': 'Agent Endpoint',
        'claw_api_key': 'Agent API Key',
        'claw_model': 'Agent Model (blank = inherit)',
        'claw_thinking': 'Agent Thinking (blank = inherit)',
        'claw_profile': 'Agent Profile',
        'claw_profile_select': 'Choose reusable Agent profile',
        'claw_soul': 'Agent Soul (blank = inherit)',
        'claw_skills': 'Agent Skills (blank = inherit)',
        'codex_endpoint': 'Codex Endpoint',
        'codex_api_key': 'Codex API Key',
        'codex_model': 'Codex Model',
        'codex_thinking': 'Codex Thinking',
        'enable_plan': 'Enable Codex Plan Mode (best effort)',
        'enable_max_permission': 'Codex Max Permission (approve-all in folder)',
        'create_button': 'Create Task',
        'active_products': 'Active Tasks',
        'no_products': 'No tasks yet. Create one on the right to get started.',
        'created_at': 'Created',
        'back': '← Back to Dashboard',
        'status': 'Status',
        'self_test': 'Self-test',
        'configuration_details': 'Configuration Details',
        'workspace_folder': 'Workspace Folder',
        'claw_setting': 'Agent Setting',
        'codex_setting': 'Codex Setting',
        'model': 'Model',
        'thinking': 'Thinking',
        'modes': 'Modes',
        'api_key_present': 'API Key Set',
        'yes': 'Yes',
        'no': 'No',
        'run_self_test': 'Run Self-Test',
        'start_continue_run': 'Start / Continue Run',
        'stop_run': 'Stop Run',
        'delete_product': 'Delete Task',
        'delete_confirm': 'Delete this task? It will be moved to trash.',
        'bulk_delete': 'Bulk Delete Selected',
        'bulk_delete_confirm': 'Delete selected tasks? Running ones will be skipped; others will be moved to trash.',
        'select_for_bulk_delete': 'Select all for bulk delete',
        'running_skip_note': 'Running tasks will be skipped',
        'append_requirement': 'Send to Agent',
        'append_placeholder': 'Send a new requirement, correction, or constraint to Agent...',
        'append_button': 'Send',
        'user_claw_dialogue': 'User ↔ Agent Dialogue',
        'claw_codex_dialogue': 'Agent ↔ Codex Dialogue',
        'no_user_claw': 'No User ↔ Agent dialogue yet.',
        'no_claw_codex': 'No Agent ↔ Codex dialogue yet.',
        'claw_log': 'Agent Log',
        'codex_log': 'Codex Log',
        'no_logs': 'No logs yet.',
        'untitled': 'Untitled Task',
        'self_test_details': 'Self-test Details',
        'not_run': 'not-run',
        'idle': 'idle',
        'running': 'running',
        'stopped': 'stopped',
        'delivered': 'delivered',
        'failed': 'failed',
        'passed': 'passed',
        'check': 'Check',
        'result': 'Result',
        'detail': 'Detail',
        'role_policy_title': 'Execution Policy',
        'role_policy_body': 'Main code and product files are written by Codex inside the product folder; Agent handles planning, supervision, networking, dataset download, requirement synthesis, and progress management, and does not directly write main product code into the product folder.',
        'claw_identity_title': 'Independent Agent Identity',
        'claw_identity_body': 'Agent is modeled as a reusable profile: the profile owns default soul / skills / model / thinking, while each product only adds local overrides.',
        'effective_claw_identity': 'Effective Agent Identity',
        'profile_name': 'Profile Name',
        'profile_description': 'Profile Description',
        'profile_soul_placeholder': 'e.g. Rigorous, efficient, pragmatic supervisor. Think like an engineer-scientist.',
        'profile_skills_placeholder': 'e.g. complex planning\nnetwork / computer / AI debugging\nautonomous exploration',
        'profile_desc_placeholder': 'What kind of work is this Agent profile good at?',
        'reusable_claw_profiles': 'Reusable Agent Profiles',
        'no_profiles': 'No profiles yet; the default Sandrone profile will be used automatically.',
        'create_profile': 'Create New Profile',
        'create_profile_button': 'Create Profile',
        'save_current_claw_profile': 'Save current Agent as reusable profile',
        'save_profile_button': 'Save as Profile',
        'profile_saved_hint': 'After saving, new projects can reuse this Agent directly.',
        'profile_label': 'Profile',
        'soul_label': 'Soul',
        'skills_label': 'Skills',
        'inherited_from_profile': 'Inherited from profile',
        'profile_model_hint': 'Profile default model',
        'profile_thinking_hint': 'Profile default thinking',
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in I18N else DEFAULT_LANG
    text = I18N[lang].get(key, I18N[DEFAULT_LANG].get(key, key))
    return text.format(**kwargs) if kwargs else text


def normalize_lang(value: str | None) -> str:
    return value if value in I18N else DEFAULT_LANG


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def slugify(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii').lower()
    base = re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-')
    while '--' in base:
        base = base.replace('--', '-')
    return base or f'product-{uuid.uuid4().hex[:8]}'


def product_dir(product_id: str) -> Path:
    return PRODUCTS / product_id


def profile_path(profile_id: str) -> Path:
    return CLAW_PROFILES / f'{profile_id}.json'


def read_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def append_log(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as fh:
        fh.write(line.rstrip() + '\n')


def default_claw_profile() -> dict:
    ts = now_iso()
    return {
        'id': DEFAULT_PROFILE_ID,
        'name': 'Sandrone Default',
        'description': 'Rigorous, efficient, pragmatic supervisor for hard engineering / network / AI work.',
        'model': 'local8317_chat/gpt-5.4',
        'thinking': 'high',
        'soul': 'Rigorous, efficient, pragmatic. Think like a scientist / engineer / programmer. Do autonomous exploration and converge to verifiable outcomes.',
        'skills': 'complex task planning\nnetwork / computer / AI debugging\nautonomous exploration\nproject supervision\nclear progress reporting',
        'createdAt': ts,
        'updatedAt': ts,
    }


def ensure_default_profile() -> None:
    path = profile_path(DEFAULT_PROFILE_ID)
    if not path.exists():
        write_json(path, default_claw_profile())


def normalize_profile(profile: dict) -> tuple[dict, bool]:
    changed = False
    base = default_claw_profile()
    for key in ['id', 'name', 'description', 'model', 'thinking', 'soul', 'skills', 'createdAt', 'updatedAt']:
        if key not in profile:
            profile[key] = base[key]
            changed = True
    return profile, changed


def list_claw_profiles() -> list[dict]:
    ensure_default_profile()
    items: list[dict] = []
    for path in sorted(CLAW_PROFILES.glob('*.json')):
        profile = read_json(path, {})
        profile, changed = normalize_profile(profile)
        if changed:
            write_json(path, profile)
        items.append(profile)
    items.sort(key=lambda x: (x.get('id') != DEFAULT_PROFILE_ID, x.get('name', '').lower()))
    return items


def load_claw_profile(profile_id: str | None) -> dict:
    ensure_default_profile()
    pid = profile_id or DEFAULT_PROFILE_ID
    path = profile_path(pid)
    if not path.exists():
        pid = DEFAULT_PROFILE_ID
        path = profile_path(pid)
    profile = read_json(path, {})
    profile, changed = normalize_profile(profile)
    if changed:
        write_json(path, profile)
    return profile


def save_claw_profile_from_form(form: dict[str, str]) -> str:
    name = form.get('profileName', '').strip() or 'Unnamed Claw Profile'
    pid = slugify(name)
    path = profile_path(pid)
    i = 2
    while path.exists():
        pid = f'{slugify(name)}-{i}'
        path = profile_path(pid)
        i += 1
    ts = now_iso()
    profile = {
        'id': pid,
        'name': name,
        'description': form.get('profileDescription', '').strip(),
        'model': form.get('profileModel', '').strip() or default_claw_profile()['model'],
        'thinking': form.get('profileThinking', '').strip() or default_claw_profile()['thinking'],
        'soul': form.get('profileSoul', '').strip() or default_claw_profile()['soul'],
        'skills': form.get('profileSkills', '').strip() or default_claw_profile()['skills'],
        'createdAt': ts,
        'updatedAt': ts,
    }
    write_json(path, profile)
    return pid


def normalize_config(cfg: dict) -> tuple[dict, bool]:
    changed = False
    if 'id' not in cfg:
        cfg['id'] = f'product-{uuid.uuid4().hex[:8]}'
        changed = True
    claw = cfg.setdefault('claw', {})
    codex = cfg.setdefault('codex', {})
    defaults = {
        'endpoint': 'http://localhost:8317/v1',
        'apiKey': '',
        'profileId': DEFAULT_PROFILE_ID,
        'model': '',
        'thinking': '',
        'soul': '',
        'skills': '',
    }
    for k, v in defaults.items():
        if k not in claw:
            claw[k] = v
            changed = True
    codex_defaults = {
        'endpoint': 'http://localhost:8317/v1',
        'apiKey': '',
        'model': 'gpt-5.4-medium',
        'thinking': 'medium',
        'planMode': True,
        'maxPermission': True,
        'sessionName': f"oc-product-{cfg['id']}",
    }
    for k, v in codex_defaults.items():
        if k not in codex:
            codex[k] = v
            changed = True
    if 'createdAt' not in cfg:
        cfg['createdAt'] = now_iso()
        changed = True
    return cfg, changed


def normalize_state(st: dict) -> tuple[dict, bool]:
    changed = False
    defaults = {
        'status': 'idle',
        'createdAt': now_iso(),
        'updatedAt': now_iso(),
        'lastRunId': None,
        'lastError': None,
        'selfTest': {'status': 'not-run', 'updatedAt': None, 'checks': {}},
        'stopRequested': False,
    }
    for k, v in defaults.items():
        if k not in st:
            st[k] = v
            changed = True
    if 'conversation' not in st:
        st['conversation'] = []
        changed = True
    conversations = st.get('conversations')
    if not isinstance(conversations, dict):
        conversations = {}
        st['conversations'] = conversations
        changed = True
    if 'userClaw' not in conversations:
        conversations['userClaw'] = []
        changed = True
    if 'clawCodex' not in conversations:
        conversations['clawCodex'] = []
        changed = True
    legacy = st.get('conversation') or []
    if legacy and not conversations['userClaw'] and not conversations['clawCodex']:
        for item in legacy:
            role = item.get('role')
            if role in {'user', 'claw'}:
                conversations['userClaw'].append(item)
            else:
                conversations['clawCodex'].append(item)
        changed = True
    return st, changed


def load_product_config(product_id: str) -> dict:
    path = product_dir(product_id) / 'config.json'
    cfg = read_json(path, {})
    cfg, changed = normalize_config(cfg)
    if changed:
        write_json(path, cfg)
    return cfg


def save_product_config(product_id: str, cfg: dict) -> None:
    cfg, _ = normalize_config(cfg)
    write_json(product_dir(product_id) / 'config.json', cfg)


def load_product_state(product_id: str) -> dict:
    path = product_dir(product_id) / 'state.json'
    st = read_json(path, {})
    st, changed = normalize_state(st)
    if changed:
        write_json(path, st)
    return st


def save_product_state(product_id: str, st: dict) -> None:
    st, _ = normalize_state(st)
    write_json(product_dir(product_id) / 'state.json', st)


def effective_claw_config(cfg: dict) -> dict:
    claw = cfg.get('claw', {})
    profile = load_claw_profile(claw.get('profileId'))
    return {
        'profileId': profile.get('id'),
        'profileName': profile.get('name'),
        'profileDescription': profile.get('description', ''),
        'endpoint': claw.get('endpoint', ''),
        'apiKey': claw.get('apiKey', ''),
        'model': claw.get('model') or profile.get('model', ''),
        'thinking': claw.get('thinking') or profile.get('thinking', ''),
        'soul': claw.get('soul') or profile.get('soul', ''),
        'skills': claw.get('skills') or profile.get('skills', ''),
    }


def list_products():
    items = []
    for d in sorted(PRODUCTS.iterdir() if PRODUCTS.exists() else []):
        if not d.is_dir():
            continue
        cfg = load_product_config(d.name)
        st = load_product_state(d.name)
        items.append({'id': d.name, 'config': cfg, 'state': st, 'effectiveClaw': effective_claw_config(cfg)})
    return items


def mask_present(value: str | None) -> str:
    return 'yes' if value else 'no'


def build_models_url(base: str) -> str:
    base = (base or '').rstrip('/')
    if not base:
        return ''
    if base.endswith('/models'):
        return base
    return f'{base}/models'


def probe_openai_like_endpoint(base_url: str, api_key: str | None = None) -> dict:
    models_url = build_models_url(base_url)
    if not models_url:
        return {'ok': False, 'detail': 'missing base url'}
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    req = Request(models_url, headers=headers, method='GET')
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read(1200).decode('utf-8', 'ignore')
            ok = 200 <= resp.status < 300
            return {'ok': ok, 'detail': f'HTTP {resp.status}: {body[:400]}'}
    except HTTPError as e:
        body = e.read(400).decode('utf-8', 'ignore') if hasattr(e, 'read') else ''
        return {'ok': False, 'detail': f'HTTPError {e.code}: {body}'}
    except URLError as e:
        return {'ok': False, 'detail': f'URLError: {e}'}
    except Exception as e:
        return {'ok': False, 'detail': str(e)}


def create_product(form: dict[str, str]) -> str:
    name = form.get('name', '').strip() or 'Untitled Product'
    product_id = slugify(name)
    d = product_dir(product_id)
    i = 2
    while d.exists():
        product_id = f"{slugify(name)}-{i}"
        d = product_dir(product_id)
        i += 1
    d.mkdir(parents=True, exist_ok=True)

    profile = load_claw_profile(form.get('clawProfileId') or DEFAULT_PROFILE_ID)
    cfg = {
        'id': product_id,
        'name': name,
        'goal': form.get('goal', '').strip(),
        'productFolder': form.get('productFolder', '').strip(),
        'claw': {
            'endpoint': form.get('clawEndpoint', '').strip(),
            'apiKey': form.get('clawApiKey', '').strip(),
            'profileId': profile.get('id'),
            'model': form.get('clawModel', '').strip(),
            'thinking': form.get('clawThinking', '').strip(),
            'soul': form.get('clawSoul', '').strip(),
            'skills': form.get('clawSkills', '').strip(),
        },
        'codex': {
            'endpoint': form.get('codexEndpoint', '').strip(),
            'apiKey': form.get('codexApiKey', '').strip(),
            'model': form.get('codexModel', '').strip() or 'gpt-5.4-medium',
            'thinking': form.get('codexThinking', '').strip() or 'medium',
            'planMode': form.get('codexPlanMode', '') == 'on',
            'maxPermission': form.get('codexMaxPermission', '') == 'on',
            'sessionName': f'oc-product-{product_id}',
        },
        'createdAt': now_iso(),
    }
    st = {
        'status': 'idle',
        'createdAt': now_iso(),
        'updatedAt': now_iso(),
        'lastRunId': None,
        'lastError': None,
        'selfTest': {
            'status': 'not-run',
            'updatedAt': None,
            'checks': {},
        },
        'conversation': [],
        'conversations': {
            'userClaw': [],
            'clawCodex': [],
        },
        'stopRequested': False,
    }
    save_product_config(product_id, cfg)
    save_product_state(product_id, st)
    append_log(d / 'logs' / 'claw.log', f'[{now_iso()}] Product created.')
    append_log(d / 'logs' / 'codex.log', f'[{now_iso()}] Product created.')
    append_user_claw_message(product_id, 'claw', f"Agent profile '{profile.get('name')}' attached to this product. Ready for user instructions.")
    return product_id


def build_codex_env(cfg: dict) -> dict:
    codex = cfg.get('codex', {})
    env = os.environ.copy()
    if codex.get('endpoint'):
        env['OPENAI_BASE_URL'] = codex['endpoint']
    if codex.get('apiKey'):
        env['OPENAI_API_KEY'] = codex['apiKey']
    env['HTTP_PROXY'] = 'http://127.0.0.1:7897'
    env['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
    env['http_proxy'] = 'http://127.0.0.1:7897'
    env['https_proxy'] = 'http://127.0.0.1:7897'
    env['NO_PROXY'] = '127.0.0.1,localhost,::1'
    env['no_proxy'] = '127.0.0.1,localhost,::1'
    return env


def update_state(product_id: str, **kwargs):
    st = load_product_state(product_id)
    st.update(kwargs)
    st['updatedAt'] = now_iso()
    save_product_state(product_id, st)


def append_user_claw_message(product_id: str, role: str, text: str):
    st = load_product_state(product_id)
    st.setdefault('conversations', {}).setdefault('userClaw', []).append({'ts': now_iso(), 'role': role, 'text': text})
    st['updatedAt'] = now_iso()
    save_product_state(product_id, st)


def append_claw_codex_message(product_id: str, role: str, text: str):
    st = load_product_state(product_id)
    st.setdefault('conversations', {}).setdefault('clawCodex', []).append({'ts': now_iso(), 'role': role, 'text': text})
    st['updatedAt'] = now_iso()
    save_product_state(product_id, st)


def append_legacy_codex_conversation(product_id: str, text: str):
    st = load_product_state(product_id)
    st.setdefault('conversation', []).append({'ts': now_iso(), 'role': 'codex', 'text': text})
    st['updatedAt'] = now_iso()
    save_product_state(product_id, st)


def active_run_info(product_id: str):
    with RUN_LOCK:
        return ACTIVE_RUNS.get(product_id)


def set_active_run(product_id: str, info: dict):
    with RUN_LOCK:
        ACTIVE_RUNS[product_id] = info


def set_active_proc(product_id: str, proc):
    with RUN_LOCK:
        info = ACTIVE_RUNS.get(product_id)
        if info is not None:
            info['proc'] = proc


def clear_active_run(product_id: str):
    with RUN_LOCK:
        ACTIVE_RUNS.pop(product_id, None)


def start_run(product_id: str) -> str:
    info = active_run_info(product_id)
    if info and info.get('thread') and info['thread'].is_alive():
        return info.get('run_id') or 'running'

    st = load_product_state(product_id)
    run_id = datetime.now().strftime('%Y%m%d-%H%M%S')
    stop_event = threading.Event()
    st.update({'status': 'running', 'updatedAt': now_iso(), 'lastRunId': run_id, 'lastError': None, 'stopRequested': False})
    save_product_state(product_id, st)
    cfg = load_product_config(product_id)
    claw_eff = effective_claw_config(cfg)
    append_user_claw_message(product_id, 'claw', f"{claw_eff.get('profileName')} accepted the run request. Preparing supervisor context for Codex.")
    t_runner = threading.Thread(target=run_supervision_loop, args=(product_id, run_id, stop_event), daemon=True)
    set_active_run(product_id, {'thread': t_runner, 'proc': None, 'run_id': run_id, 'stop_event': stop_event})
    t_runner.start()
    return run_id


def stop_run(product_id: str) -> bool:
    info = active_run_info(product_id)
    if not info:
        update_state(product_id, status='stopped', stopRequested=True)
        append_user_claw_message(product_id, 'claw', 'Stop requested while no active Codex subprocess was found. Product marked stopped.')
        return False
    info['stop_event'].set()
    update_state(product_id, stopRequested=True)
    append_user_claw_message(product_id, 'claw', 'Stop requested by user. Agent is terminating the active Codex run.')
    proc = info.get('proc')
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
    return True


def delete_product(product_id: str) -> tuple[bool, str]:
    info = active_run_info(product_id)
    if info and info.get('thread') and info['thread'].is_alive():
        return False, 'running'
    src = product_dir(product_id)
    if not src.exists():
        return False, 'missing'
    dst = TRASH / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{product_id}"
    shutil.move(str(src), str(dst))
    return True, str(dst)


def start_self_test(product_id: str) -> None:
    t_runner = threading.Thread(target=run_self_test, args=(product_id,), daemon=True)
    t_runner.start()


def save_current_product_claw_as_profile(product_id: str, form: dict[str, str]) -> str:
    cfg = load_product_config(product_id)
    claw_eff = effective_claw_config(cfg)
    name = form.get('profileName', '').strip() or f"{cfg.get('name', 'product')} agent"
    pid = slugify(name)
    path = profile_path(pid)
    i = 2
    while path.exists():
        pid = f'{slugify(name)}-{i}'
        path = profile_path(pid)
        i += 1
    ts = now_iso()
    profile = {
        'id': pid,
        'name': name,
        'description': form.get('profileDescription', '').strip() or f"Saved from product {cfg.get('name', product_id)}",
        'model': claw_eff.get('model', ''),
        'thinking': claw_eff.get('thinking', ''),
        'soul': claw_eff.get('soul', ''),
        'skills': claw_eff.get('skills', ''),
        'createdAt': ts,
        'updatedAt': ts,
    }
    write_json(path, profile)
    cfg.setdefault('claw', {})['profileId'] = pid
    cfg['claw']['model'] = ''
    cfg['claw']['thinking'] = ''
    cfg['claw']['soul'] = ''
    cfg['claw']['skills'] = ''
    save_product_config(product_id, cfg)
    append_user_claw_message(product_id, 'claw', f"Current Agent identity was saved as reusable profile '{profile['name']}'. Future products can reuse it directly.")
    return pid


def run_self_test(product_id: str) -> None:
    d = product_dir(product_id)
    cfg = load_product_config(product_id)
    st = load_product_state(product_id)
    claw_log = d / 'logs' / 'claw.log'
    codex_log = d / 'logs' / 'codex.log'
    product_folder = cfg.get('productFolder') or '/tmp'
    codex = cfg.get('codex', {})
    claw_eff = effective_claw_config(cfg)
    session_name = codex.get('sessionName') or f'oc-product-{product_id}'
    env = build_codex_env(cfg)

    def log_claw(text: str):
        append_log(claw_log, f'[{now_iso()}] {text}')

    def log_codex(text: str):
        append_log(codex_log, f'[{now_iso()}] {text}')

    log_claw('Starting self-test.')
    st.setdefault('selfTest', {})
    st['selfTest'] = {'status': 'running', 'updatedAt': now_iso(), 'checks': {}}
    save_product_state(product_id, st)

    checks = {}

    checks['agent_config'] = {
        'ok': bool(claw_eff.get('endpoint') and claw_eff.get('model')),
        'detail': f"profile={claw_eff.get('profileName','-')} endpoint={claw_eff.get('endpoint','-')} model={claw_eff.get('model','-')} thinking={claw_eff.get('thinking','-')} apiKey={'yes' if claw_eff.get('apiKey') else 'no'}",
    }
    log_claw(f"Self-test agent_config: {checks['agent_config']}")

    checks['agent_connection'] = probe_openai_like_endpoint(claw_eff.get('endpoint', ''), claw_eff.get('apiKey'))
    log_claw(f"Self-test agent_connection: {checks['agent_connection']['ok']}")

    checks['product_folder'] = {'ok': Path(product_folder).exists(), 'detail': product_folder}
    log_claw(f"Self-test product_folder: {checks['product_folder']}")

    try:
        r = subprocess.run([str(ACPX), '--cwd', product_folder, 'codex', 'sessions', 'ensure', '--name', session_name], env=env, check=False, capture_output=True, text=True, timeout=120)
        out = (r.stdout or '') + (('\n' + r.stderr) if r.stderr else '')
        log_codex(out)
        checks['codex_session'] = {'ok': r.returncode == 0, 'detail': out[-500:]}
    except Exception as e:
        checks['codex_session'] = {'ok': False, 'detail': str(e)}
    log_claw(f"Self-test codex_session: {checks['codex_session']['ok']}")

    try:
        r = subprocess.run([str(ACPX), '--cwd', product_folder, 'codex', 'status', '--session', session_name], env=env, check=False, capture_output=True, text=True, timeout=120)
        out = (r.stdout or '') + (('\n' + r.stderr) if r.stderr else '')
        log_codex(out)
        checks['codex_status'] = {'ok': r.returncode == 0 and 'status:' in out, 'detail': out[-500:]}
    except Exception as e:
        checks['codex_status'] = {'ok': False, 'detail': str(e)}
    log_claw(f"Self-test codex_status: {checks['codex_status']['ok']}")

    try:
        r = subprocess.run([str(ACPX), '--cwd', product_folder, '--approve-all', '--non-interactive-permissions', 'deny', 'codex', 'exec', 'Reply with exactly SELFTEST_CODEX_OK'], env=env, check=False, capture_output=True, text=True, timeout=300)
        out = (r.stdout or '') + (('\n' + r.stderr) if r.stderr else '')
        log_codex(out)
        checks['codex_prompt'] = {'ok': r.returncode == 0 and 'SELFTEST_CODEX_OK' in out, 'detail': out[-500:]}
    except Exception as e:
        checks['codex_prompt'] = {'ok': False, 'detail': str(e)}
    log_claw(f"Self-test codex_prompt: {checks['codex_prompt']['ok']}")

    overall = all(v.get('ok') for v in checks.values())
    st = load_product_state(product_id)
    st['selfTest'] = {'status': 'passed' if overall else 'failed', 'updatedAt': now_iso(), 'checks': checks}
    save_product_state(product_id, st)
    append_user_claw_message(product_id, 'claw', f"Self-test finished: {'passed' if overall else 'failed'}.")
    log_claw(f"Self-test finished: {'passed' if overall else 'failed'}.")


def run_codex_command(cmd: list[str], env: dict, timeout_seconds: int, stop_event: threading.Event, product_id: str):
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    set_active_proc(product_id, proc)
    start = time.time()
    while True:
        if stop_event.is_set():
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except Exception:
                stdout, stderr = '', ''
            return -15, (stdout or '') + (('\n' + stderr) if stderr else ''), True
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            return proc.returncode, (stdout or '') + (('\n' + stderr) if stderr else ''), False
        if time.time() - start > timeout_seconds:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except Exception:
                stdout, stderr = '', ''
            return 124, (stdout or '') + (('\n' + stderr) if stderr else ''), False
        time.sleep(1)


def summarize_user_claw_messages(st: dict, limit: int = 8) -> str:
    user_msgs = [x.get('text', '') for x in st.get('conversations', {}).get('userClaw', []) if x.get('role') == 'user']
    return '\n'.join(f'- {x}' for x in user_msgs[-limit:]) or '- none'


def claw_identity_block(cfg: dict) -> str:
    claw_eff = effective_claw_config(cfg)
    return (
        f"Supervisor identity name: {claw_eff.get('profileName')}\n"
        f"Supervisor soul: {claw_eff.get('soul')}\n"
        f"Supervisor skills/priorities: {claw_eff.get('skills')}\n"
        f"Supervisor model preference: {claw_eff.get('model')}\n"
        f"Supervisor thinking preference: {claw_eff.get('thinking')}\n"
        "You are an independent supervisor identity that may be reused across multiple products. Codex is the implementation executor, not the same thing as you."
    )


def run_supervision_loop(product_id: str, run_id: str, stop_event: threading.Event) -> None:
    d = product_dir(product_id)
    cfg = load_product_config(product_id)
    state_path = d / 'state.json'
    claw_log = d / 'logs' / 'claw.log'
    codex_log = d / 'logs' / 'codex.log'
    product_folder = cfg.get('productFolder') or '/tmp'
    codex = cfg.get('codex', {})
    claw_eff = effective_claw_config(cfg)
    session_name = codex.get('sessionName') or f'oc-product-{product_id}'
    env = build_codex_env(cfg)

    def set_state(**kwargs):
        st = load_product_state(product_id)
        st.update(kwargs)
        st['updatedAt'] = now_iso()
        save_product_state(product_id, st)

    def log_claw(text: str):
        append_log(claw_log, f'[{now_iso()}] {text}')

    def log_codex(text: str):
        append_log(codex_log, f'[{now_iso()}] {text}')

    try:
        log_claw(f'Starting run {run_id}. Goal: {cfg.get("goal", "")}'.strip())
        log_claw(f"Execution policy: Codex is the primary author of product code inside the product folder; {claw_eff.get('profileName')} supervises, plans, researches, and coordinates.")
        append_user_claw_message(product_id, 'claw', f"{claw_eff.get('profileName')} started run {run_id}. I will supervise Codex and keep the product state consistent.")
        append_claw_codex_message(product_id, 'claw', f"Run {run_id} opened. Supervisor identity: {claw_eff.get('profileName')}.")
        log_claw('Ensuring persistent Codex session exists.')
        subprocess.run([str(ACPX), '--cwd', product_folder, 'codex', 'sessions', 'ensure', '--name', session_name], env=env, check=False, capture_output=True, text=True, timeout=120)

        if codex.get('planMode'):
            log_claw('Attempting to enable Codex plan mode (best effort).')
            r = subprocess.run([str(ACPX), '--cwd', product_folder, 'codex', 'set-mode', 'plan', '--session', session_name], env=env, check=False, capture_output=True, text=True, timeout=120)
            log_codex((r.stdout or '') + (('\n' + r.stderr) if r.stderr else ''))
            if r.returncode != 0 or 'Invalid params' in ((r.stdout or '') + (r.stderr or '')):
                log_claw('Codex plan mode is not supported by the current backend/session; continuing without enforced plan mode.')
                append_claw_codex_message(product_id, 'claw', 'Plan-mode request was rejected by backend/session; continuing without forced plan mode.')

        if codex.get('model'):
            log_claw(f"Attempting to set Codex model to {codex['model']} (best effort).")
            r = subprocess.run([str(ACPX), '--cwd', product_folder, 'codex', 'set', 'model', codex['model'], '--session', session_name], env=env, check=False, capture_output=True, text=True, timeout=120)
            log_codex((r.stdout or '') + (('\n' + r.stderr) if r.stderr else ''))
            if r.returncode != 0 or 'Invalid params' in ((r.stdout or '') + (r.stderr or '')):
                log_claw('Codex model override was not accepted; proceeding with backend default.')

        if codex.get('thinking'):
            log_claw(f"Attempting to set Codex thinking to {codex['thinking']} (best effort).")
            r = subprocess.run([str(ACPX), '--cwd', product_folder, 'codex', 'set', 'thinking', codex['thinking'], '--session', session_name], env=env, check=False, capture_output=True, text=True, timeout=120)
            log_codex((r.stdout or '') + (('\n' + r.stderr) if r.stderr else ''))
            if r.returncode != 0 or 'Invalid params' in ((r.stdout or '') + (r.stderr or '')):
                log_claw('Codex thinking override was not accepted by the current backend; proceeding without explicit thinking override.')

        if codex.get('maxPermission'):
            log_claw('Using approve-all permission mode for Codex runs.')

        st = load_product_state(product_id)
        user_context = summarize_user_claw_messages(st)
        prompt = (
            f"You are the implementation executor for task '{cfg.get('name')}'.\n"
            f"Goal: {cfg.get('goal')}\n"
            f"{claw_identity_block(cfg)}\n"
            f"Additional user requests accumulated in the User↔Agent thread:\n{user_context}\n"
            f"Work only inside: {product_folder}\n"
            f"You are the primary author of product code and product files in that folder. Agent is not writing the main product code for you.\n"
            f"If external information, networking, dataset download, or planning is needed, treat that as supervisor support context, but the actual product implementation work must be done by you inside the product folder.\n"
            f"Produce a real deliverable in that folder if possible. If additional steps are needed, continue iteratively. When the product is actually delivered, include the exact token DELIVERED_OK. If it cannot be completed, include the exact token FAILED_FINAL and explain why."
        )
        cmd_prefix = [str(ACPX), '--cwd', product_folder]
        if codex.get('maxPermission'):
            cmd_prefix += ['--approve-all', '--non-interactive-permissions', 'deny']

        for turn in range(1, 6):
            if stop_event.is_set():
                log_claw('Stop requested before next Codex turn. Marking stopped.')
                append_user_claw_message(product_id, 'claw', f"{claw_eff.get('profileName')} stopped before dispatching the next Codex turn.")
                set_state(status='stopped', stopRequested=True)
                return
            set_state(status='running', stopRequested=False)
            dispatch_text = prompt if turn == 1 else 'Continue from the current product context and any newly appended user requests. Agent remains the independent supervisor identity; Codex remains the primary code author. Either make further progress, deliver with DELIVERED_OK, or stop with FAILED_FINAL.'
            log_claw(f'Dispatching Codex turn {turn}.')
            append_claw_codex_message(product_id, 'claw', f"Dispatch turn {turn}. Supervisor brief:\n{dispatch_text[:2400]}")
            run_cmd = cmd_prefix + ['codex', '--session', session_name, dispatch_text]
            rc, out, was_stopped = run_codex_command(run_cmd, env, 1800, stop_event, product_id)
            log_codex(out)
            append_claw_codex_message(product_id, 'codex', out[-3000:])
            append_legacy_codex_conversation(product_id, out[-3000:])
            set_active_proc(product_id, None)
            if was_stopped:
                log_claw('Codex run stopped by user request. Marking stopped.')
                append_user_claw_message(product_id, 'claw', f"{claw_eff.get('profileName')} confirmed the Codex run was stopped by user request.")
                set_state(status='stopped', stopRequested=True)
                return
            if 'DELIVERED_OK' in out and rc == 0:
                log_claw(f'Codex reported delivered on turn {turn}. Marking delivered.')
                append_user_claw_message(product_id, 'claw', f"Codex reported delivery on turn {turn}. Product marked delivered.")
                set_state(status='delivered', stopRequested=False)
                return
            if 'FAILED_FINAL' in out:
                log_claw(f'Codex reported final failure on turn {turn}. Marking failed.')
                append_user_claw_message(product_id, 'claw', f"Codex declared final failure on turn {turn}. Product marked failed.")
                set_state(status='failed', lastError='codex declared final failure', stopRequested=False)
                return
            if rc != 0:
                log_claw(f'Codex returned non-zero exit on turn {turn} ({rc}).')
                append_user_claw_message(product_id, 'claw', f"Codex turn {turn} returned non-zero exit {rc}. Agent will retry if budget remains.")
                if turn >= 5:
                    set_state(status='failed', lastError=f'codex exit {rc}', stopRequested=False)
                    return
                time.sleep(2)
                continue
            append_user_claw_message(product_id, 'claw', f"Codex turn {turn} completed without terminal token. Agent is continuing supervision.")
            log_claw(f'Codex turn {turn} completed without terminal token; continuing supervision loop.')
            time.sleep(2)

        log_claw('Reached supervision turn limit without delivery/final failure. Marking failed for now.')
        append_user_claw_message(product_id, 'claw', 'Supervision turn limit reached without delivery or final failure. Product marked failed for now.')
        set_state(status='failed', lastError='turn limit reached without terminal result', stopRequested=False)
    except Exception as e:
        log_claw(f'Run failed with exception: {e}')
        append_user_claw_message(product_id, 'claw', f'Run failed with exception: {e}')
        set_state(status='failed', lastError=str(e), stopRequested=False)
    finally:
        clear_active_run(product_id)


def language_switch_html(current_lang: str, base_path: str) -> str:
    return f"""
    <div class="lang-switch">
      <a href="{html.escape(base_path)}?lang=en" class="lang-item {'active' if current_lang == 'en' else ''}">EN</a>
      <a href="{html.escape(base_path)}?lang=zh" class="lang-item {'active' if current_lang == 'zh' else ''}">中</a>
    </div>
    """


def page_template(title: str, body: str, lang: str, path: str = '/') -> bytes:
    html_lang = 'zh-CN' if lang == 'zh' else 'en'
    lang_switch = language_switch_html(lang, path)
    return f"""
<!doctype html>
<html lang="{html.escape(html_lang)}" data-theme="light">
<head>
  <meta charset='utf-8'>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-hover: #f1f5f9;
      --surface-sunken: #f8fafc;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --border-focus: #cbd5e1;
      --primary: #0f172a;
      --primary-hover: #000000;
      --primary-text: #ffffff;
      --accent: #2563eb;
      --danger: #dc2626;
      --danger-bg: #fef2f2;
      --danger-hover: #fee2e2;
      --success: #059669;
      --success-bg: #ecfdf5;
      --warning: #d97706;
      --warning-bg: #fffbeb;
      --radius: 12px;
      --radius-sm: 8px;
      --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.08);
      --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.05);
      --terminal-bg: #0f172a;
      --terminal-text: #e2e8f0;
    }}

    [data-theme="dark"] {{
      --bg: #0a0a0b;
      --surface: #121214;
      --surface-hover: #1b1b1f;
      --surface-sunken: #0b0b0d;
      --text-main: #ededed;
      --text-muted: #a1a1aa;
      --border: #27272a;
      --border-focus: #3f3f46;
      --primary: #ffffff;
      --primary-hover: #e5e7eb;
      --primary-text: #000000;
      --accent: #60a5fa;
      --danger: #f87171;
      --danger-bg: rgba(239, 68, 68, 0.12);
      --danger-hover: rgba(239, 68, 68, 0.2);
      --success: #34d399;
      --success-bg: rgba(16, 185, 129, 0.12);
      --warning: #fbbf24;
      --warning-bg: rgba(245, 158, 11, 0.12);
      --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
      --shadow-md: 0 8px 20px rgba(0, 0, 0, 0.35);
      --terminal-bg: #000000;
      --terminal-text: #d4d4d8;
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.55;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.25s ease, color 0.25s ease;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .mono {{ font-family: 'JetBrains Mono', Consolas, monospace; font-size: 0.86em; word-break: break-word; }}
    .text-muted, .muted {{ color: var(--text-muted); }}
    h1, h2, h3 {{ margin: 0; font-weight: 600; letter-spacing: -0.015em; }}

    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 999px; border: 2px solid var(--bg); }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

    .app-header {{
      position: sticky;
      top: 0;
      z-index: 40;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      height: 64px;
      padding: 0 24px;
      background: color-mix(in srgb, var(--surface) 90%, transparent);
      border-bottom: 1px solid var(--border);
      backdrop-filter: blur(8px);
    }}
    .header-logo {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
      font-size: 1.1rem;
      letter-spacing: -0.02em;
      color: var(--text-main);
    }}
    .header-actions {{ display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
    .container {{ max-width: 1460px; margin: 0 auto; padding: 28px 24px 40px; }}

    .dashboard-grid {{ display: grid; grid-template-columns: 1fr; gap: 32px; align-items: start; }}
    .two-col {{ display: grid; grid-template-columns: 1fr; gap: 24px; }}
    .three-col {{ display: grid; grid-template-columns: 1fr; gap: 24px; }}
    @media (min-width: 1080px) {{
      /* Layout swapped: Main content left, Sidebar right */
      .dashboard-grid {{ grid-template-columns: minmax(0, 1fr) 420px; }}
      .two-col {{ grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }}
      .three-col {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    }}
    
    .sticky-panel {{
      position: sticky;
      top: 92px;
      align-self: start;
      display: grid;
      grid-template-rows: auto;
      gap: 20px;
      max-height: calc(100vh - 112px);
      overflow-y: auto;
      padding-right: 4px;
    }}
    @media (max-width: 1079px) {{ .sticky-panel {{ position: static; display: flex; flex-direction: column; max-height: none; overflow: visible; }} }}

    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      overflow: visible;
      transition: box-shadow 0.2s ease;
    }}
    .card:hover {{ box-shadow: var(--shadow-md); }}
    .sidebar-card {{ display: flex; flex-direction: column; }}
    .card-header {{
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      background: color-mix(in srgb, var(--surface) 95%, var(--surface-hover));
      border-radius: var(--radius) var(--radius) 0 0;
    }}
    .card-title {{ font-size: 0.95rem; font-weight: 700; color: var(--text-main); text-transform: uppercase; letter-spacing: 0.03em; display: flex; align-items: center; gap: 8px; }}
    .card-body {{ padding: 20px; }}

    label {{ display: block; margin-bottom: 6px; font-size: 0.86rem; font-weight: 600; color: var(--text-main); }}
    input[type="text"], input[type="password"], input:not([type]), textarea, select {{
      width: 100%;
      max-width: 100%;
      display: block;
      padding: 10px 14px;
      margin-bottom: 16px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      background: var(--surface-sunken);
      color: var(--text-main);
      font: inherit;
      transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
    }}
    textarea {{ resize: vertical; min-height: 92px; }}
    select {{
      appearance: none;
      background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
      background-repeat: no-repeat;
      background-position: right 12px center;
      background-size: 16px;
      padding-right: 40px;
    }}
    input:focus, textarea:focus, select:focus {{
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 15%, transparent);
      background: var(--surface);
    }}
    .form-row {{ display: grid; grid-template-columns: 1fr; gap: 14px; }}
    @media (min-width: 700px) {{ .form-row {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    .settings-group {{
      background: var(--surface-sunken);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px;
      margin-bottom: 16px;
    }}
    .settings-group-title {{
      margin-bottom: 12px;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      font-weight: 700;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 9px 16px;
      border-radius: var(--radius-sm);
      border: 1px solid transparent;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.1s ease, background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
      white-space: nowrap;
    }}
    .btn:active {{ transform: scale(0.98); }}
    .btn:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none; }}
    .btn-primary {{ background: var(--primary); color: var(--primary-text); box-shadow: var(--shadow-sm); }}
    .btn-primary:hover:not(:disabled) {{ background: var(--primary-hover); box-shadow: var(--shadow-md); }}
    .btn-secondary {{ background: var(--surface); color: var(--text-main); border-color: var(--border); box-shadow: var(--shadow-sm); }}
    .btn-secondary:hover:not(:disabled) {{ background: var(--surface-hover); border-color: var(--border-focus); }}
    .btn-danger {{ background: var(--danger-bg); color: var(--danger); border-color: transparent; }}
    .btn-danger:hover:not(:disabled) {{ background: var(--danger-hover); }}
    .btn-icon {{ padding: 9px; min-width: 38px; min-height: 38px; }}

    .checkbox-line {{ display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; color: var(--text-main); font-size: 0.92rem; font-weight: 500; cursor: pointer; }}
    .checkbox-line input {{ margin-top: 3px; cursor: pointer; }}

    .lang-switch {{ display: flex; align-items: center; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface-sunken); flex-shrink: 0; }}
    .lang-item {{ display: inline-flex; align-items: center; justify-content: center; min-width: 44px; padding: 4px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; color: var(--text-muted); transition: all 0.2s ease; }}
    .lang-item.active {{ background: var(--surface); color: var(--text-main); box-shadow: var(--shadow-sm); font-weight: 700; }}
    .lang-item:hover:not(.active) {{ text-decoration: none; color: var(--text-main); background: color-mix(in srgb, var(--surface) 50%, transparent); }}

    .view-header {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
    .view-header h1 {{ font-size: 1.85rem; line-height: 1.2; letter-spacing: -0.03em; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
    .view-header h2 {{ font-size: 1.3rem; margin-bottom: 4px; color: var(--text-main); }}
    .view-header-actions {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .back-link {{ display: inline-flex; align-items: center; gap: 6px; margin-bottom: 16px; color: var(--text-muted); font-weight: 600; font-size: 0.9rem; transition: color 0.2s ease; }}
    .back-link:hover {{ color: var(--text-main); text-decoration: none; }}
    .page-subtitle {{ margin-top: 6px; color: var(--text-muted); font-size: 0.95rem; max-width: 860px; }}

    .list-toolbar {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; padding: 12px 16px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow-sm); }}
    .toolbar-left, .toolbar-right {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}

    .product-list {{ border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); overflow: hidden; box-shadow: var(--shadow-sm); }}
    .product-row {{ display: flex; gap: 14px; align-items: flex-start; padding: 18px 20px; border-bottom: 1px solid var(--border); cursor: pointer; transition: background 0.2s ease; }}
    .product-row:last-child {{ border-bottom: none; }}
    .product-row:hover {{ background: var(--surface-hover); }}
    .product-row input[type=checkbox] {{ margin-top: 4px; cursor: pointer; }}
    .product-content {{ flex: 1; min-width: 0; }}
    .product-header {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; flex-wrap: wrap; margin-bottom: 6px; }}
    .product-title {{ margin: 0; font-size: 1.05rem; font-weight: 600; color: var(--text-main); word-break: break-word; line-height: 1.3; }}
    .product-desc {{ margin-bottom: 10px; color: var(--text-muted); font-size: 0.9rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }}
    .product-meta {{ display: flex; gap: 12px 16px; flex-wrap: wrap; color: var(--text-muted); font-size: 0.82rem; }}

    .badge {{ display: inline-flex; align-items: center; justify-content: center; padding: 4px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; border: 1px solid transparent; white-space: nowrap; }}
    .badge-running {{ background: rgba(37, 99, 235, 0.1); color: var(--accent); border-color: rgba(37, 99, 235, 0.2); }}
    .badge-delivered {{ background: var(--success-bg); color: var(--success); border-color: rgba(5, 150, 105, 0.22); }}
    .badge-failed {{ background: var(--danger-bg); color: var(--danger); border-color: rgba(220, 38, 38, 0.18); }}
    .badge-idle {{ background: var(--surface-sunken); color: var(--text-muted); border-color: var(--border); }}
    .badge-stopped {{ background: var(--warning-bg); color: var(--warning); border-color: rgba(217, 119, 6, 0.18); }}

    .dialogue-shell {{ background: var(--surface-sunken); max-height: 520px; overflow-y: auto; overflow-x: hidden; padding: 20px; border-radius: 0 0 var(--radius) var(--radius); }}
    .chat-bubble {{ max-width: 90%; padding: 12px 16px; border-radius: 14px; margin-bottom: 16px; font-size: 0.92rem; border: 1px solid var(--border); overflow-wrap: break-word; }}
    .bubble-bot {{ background: var(--surface); border-bottom-left-radius: 6px; margin-right: auto; box-shadow: var(--shadow-sm); }}
    .bubble-user {{ background: color-mix(in srgb, var(--accent) 8%, var(--surface)); border-color: color-mix(in srgb, var(--accent) 20%, transparent); border-bottom-right-radius: 6px; margin-left: auto; box-shadow: var(--shadow-sm); }}
    .bubble-header {{ display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; font-size: 0.75rem; }}
    .role-claw {{ color: var(--success); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
    .role-user {{ color: var(--accent); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
    .role-codex {{ color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
    .convo-text {{ white-space: pre-wrap; line-height: 1.5; }}

    .data-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    .data-table th, .data-table td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
    .data-table th {{ color: var(--text-muted); font-size: 0.84rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: var(--surface-hover); }}
    .data-table th:nth-child(1) {{ width: 28%; border-radius: 8px 0 0 0; }}
    .data-table th:nth-child(2) {{ width: 14%; }}
    .data-table th:nth-child(3) {{ width: 58%; border-radius: 0 8px 0 0; }}
    .data-table tr:last-child td {{ border-bottom: none; }}

    .terminal-window {{ background: var(--terminal-bg); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; display: flex; flex-direction: column; min-height: 340px; box-shadow: var(--shadow-md); }}
    .terminal-header {{ display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.08); }}
    .terminal-dot {{ width: 12px; height: 12px; border-radius: 999px; flex-shrink: 0; }}
    .dot-r {{ background: #ff5f56; box-shadow: 0 0 4px rgba(255,95,86,0.3); }}
    .dot-y {{ background: #ffbd2e; box-shadow: 0 0 4px rgba(255,189,46,0.3); }}
    .dot-g {{ background: #27c93f; box-shadow: 0 0 4px rgba(39,201,63,0.3); }}
    .terminal-body {{ padding: 16px; max-height: 360px; overflow-y: auto; overflow-x: auto; color: var(--terminal-text); font-size: 0.85rem; line-height: 1.6; white-space: pre-wrap; word-break: break-all; }}

    .empty-state {{ text-align: center; padding: 48px 24px; color: var(--text-muted); border: 1px dashed var(--border-focus); border-radius: var(--radius); background: var(--surface-sunken); font-size: 0.95rem; font-weight: 500; }}
    .mini {{ font-size: 0.8rem; }}
  </style>
</head>
<body>
  <header class="app-header">
    <div class="header-logo">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent);"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
      <span>TaskCaptain <span style="font-weight: 500; color: var(--text-muted);">Workspace</span></span>
    </div>
    <div class="header-actions">
      {lang_switch}
      <button class="btn btn-secondary btn-icon" type="button" onclick="toggleTheme()" title="Toggle Light/Dark Theme" style="border-radius: 999px;">
        <svg id="theme-icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        <svg id="theme-icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
      </button>
    </div>
  </header>

  <div class="container">{body}</div>

  <script>
    function applyTheme(theme) {{
      const root = document.documentElement;
      const sun = document.getElementById('theme-icon-sun');
      const moon = document.getElementById('theme-icon-moon');
      root.setAttribute('data-theme', theme);
      if (sun) sun.style.display = theme === 'light' ? 'block' : 'none';
      if (moon) moon.style.display = theme === 'dark' ? 'block' : 'none';
    }}
    function toggleTheme() {{
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('claw-theme', next);
    }}
    (function() {{
      const saved = localStorage.getItem('claw-theme');
      applyTheme(saved || 'light');
    }})();
    function toggleAllCheckboxes(source) {{
      document.querySelectorAll('.item-checkbox:not([disabled])').forEach(cb => cb.checked = source.checked);
    }}
  </script>
</body>
</html>
""".encode('utf-8')


def render_dialogue(items: list[dict], empty_text: str) -> str:
    if not items:
        return f'<div class="empty-state">{html.escape(empty_text)}</div>'
    rows = []
    for x in items:
        role = x.get('role', '')
        is_user = role == 'user'
        bubble_class = 'bubble-user' if is_user else 'bubble-bot'
        role_class = 'role-user' if role == 'user' else ('role-claw' if role == 'claw' else 'role-codex')
        role_display = 'AGENT' if role == 'claw' else role.upper()
        rows.append(f"""
        <div class='chat-bubble {bubble_class}'>
          <div class='bubble-header'>
            <span class='{role_class}'>{html.escape(role_display)}</span>
            <span class='text-muted mono'>{html.escape(x.get('ts', ''))}</span>
          </div>
          <div class='mono convo-text'>{html.escape(x.get('text', ''))}</div>
        </div>
        """)
    return ''.join(rows)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        lang = normalize_lang(parse_qs(parsed.query).get('lang', [DEFAULT_LANG])[0])
        if parsed.path == '/':
            return self.render_index(lang)
        if parsed.path.startswith('/product/'):
            pid = parsed.path.split('/')[-1]
            return self.render_product(pid, lang)
        if parsed.path == '/api/products':
            return self.send_json({'products': list_products()})
        if parsed.path == '/api/profiles':
            return self.send_json({'profiles': list_claw_profiles()})
        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length).decode('utf-8')
        parsed_form = parse_qs(raw)
        form = {k: v[0] for k, v in parsed_form.items()}
        lang = normalize_lang(form.get('lang'))
        if parsed.path == '/create':
            pid = create_product(form)
            self.redirect(f'/product/{pid}?lang={lang}')
            return
        if parsed.path == '/profiles/create':
            save_claw_profile_from_form(form)
            self.redirect(f'/?lang={lang}')
            return
        if parsed.path == '/bulk-delete':
            for pid in parsed_form.get('productIds', []):
                try:
                    delete_product(pid)
                except Exception:
                    pass
            self.redirect(f'/?lang={lang}')
            return
        if parsed.path.startswith('/start/'):
            pid = parsed.path.split('/')[-1]
            start_run(pid)
            self.redirect(f'/product/{pid}?lang={lang}')
            return
        if parsed.path.startswith('/stop/'):
            pid = parsed.path.split('/')[-1]
            stop_run(pid)
            self.redirect(f'/product/{pid}?lang={lang}')
            return
        if parsed.path.startswith('/delete/'):
            pid = parsed.path.split('/')[-1]
            ok, _ = delete_product(pid)
            if ok:
                self.redirect(f'/?lang={lang}')
            else:
                self.redirect(f'/product/{pid}?lang={lang}')
            return
        if parsed.path.startswith('/selftest/'):
            pid = parsed.path.split('/')[-1]
            start_self_test(pid)
            self.redirect(f'/product/{pid}?lang={lang}')
            return
        if parsed.path.startswith('/append-user/'):
            pid = parsed.path.split('/')[-1]
            text = form.get('message', '').strip()
            if text:
                cfg = load_product_config(pid)
                claw_eff = effective_claw_config(cfg)
                append_user_claw_message(pid, 'user', text)
                append_user_claw_message(pid, 'claw', f"{claw_eff.get('profileName')} received this instruction and will incorporate it into the next supervision / Codex dispatch cycle.")
                append_log(product_dir(pid) / 'logs' / 'claw.log', f'[{now_iso()}] User -> Agent: {text}')
            self.redirect(f'/product/{pid}?lang={lang}')
            return
        if parsed.path.startswith('/save-profile/'):
            pid = parsed.path.split('/')[-1]
            save_current_product_claw_as_profile(pid, form)
            self.redirect(f'/product/{pid}?lang={lang}')
            return
        self.send_error(404)

    def render_index(self, lang: str):
        items = list_products()
        profiles = list_claw_profiles()
        default_profile = load_claw_profile(DEFAULT_PROFILE_ID)

        def status_class(status: str) -> str:
            if status == 'running':
                return 'badge-running'
            if status in {'delivered', 'passed'}:
                return 'badge-delivered'
            if status == 'failed':
                return 'badge-failed'
            if status == 'stopped':
                return 'badge-stopped'
            return 'badge-idle'

        product_rows = []
        for item in items:
            cfg = item['config']
            st = item['state']
            claw_eff = item['effectiveClaw']
            pid = cfg.get('id')
            status = st.get('status', 'idle')
            is_running = status == 'running' and bool(active_run_info(pid))
            goal_text = cfg.get('goal', '') or '—'
            product_rows.append(f"""
            <label class='product-row' onclick="if(event.target.type!=='checkbox')window.location='/product/{pid}?lang={lang}'">
              <input class='item-checkbox' type='checkbox' name='productIds' value='{html.escape(pid)}' {'disabled' if is_running else ''} onclick='event.stopPropagation()' />
              <div class='product-content'>
                <div class='product-header'>
                  <div>
                    <div class='product-title'>{html.escape(cfg.get('name', t(lang, 'untitled')))}</div>
                    <div class='mini muted' style='margin-top: 2px;'>{html.escape(t(lang, 'profile_label'))}: {html.escape(claw_eff.get('profileName', '-'))}</div>
                  </div>
                  <span class='badge {status_class(status)}'>{html.escape(t(lang, status) if status in I18N[lang] else status)}</span>
                </div>
                <div class='product-desc'>{html.escape(goal_text)}</div>
                <div class='product-meta'>
                  <span>{html.escape(t(lang, 'created_at'))}: {html.escape(cfg.get('createdAt', ''))}</span>
                  <span>Agent: {html.escape(claw_eff.get('model', '-'))}</span>
                  <span>Codex: {html.escape(cfg.get('codex', {}).get('model', '-'))}</span>
                </div>
              </div>
            </label>
            """)

        profiles_html = ''.join(
            f"""
            <div class='card' style='transition: transform 0.2s ease; cursor: default;'>
              <div class='card-body' style='padding:18px 20px;'>
                <div style='display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap;'>
                  <div style='flex: 1; min-width: 0;'>
                    <div style='font-weight:700; margin-bottom:6px; color: var(--text-main); font-size: 1rem;'>{html.escape(p.get('name', ''))}</div>
                    <div class='text-muted mini' style='line-height: 1.5;'>{html.escape(p.get('description', ''))}</div>
                  </div>
                  <div class='text-muted mini' style='text-align: right; background: var(--surface-sunken); padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border);'>
                    <b>{html.escape(p.get('model', ''))}</b><br/>
                    Thinking: {html.escape(p.get('thinking', ''))}
                  </div>
                </div>
              </div>
            </div>
            """
            for p in profiles
        ) or f'<div class="empty-state">{html.escape(t(lang, "no_profiles"))}</div>'

        profile_options = ''.join(
            f"<option value='{html.escape(p.get('id', ''))}'>{html.escape(p.get('name', ''))}</option>" for p in profiles
        )

        body = f"""
<div class='view-header'>
  <div>
    <h1>{html.escape(t(lang, 'app_title'))}</h1>
    <div class='page-subtitle'>{html.escape(t(lang, 'app_subtitle'))}</div>
  </div>
</div>

<div class='dashboard-grid'>
  <!-- 左侧/主要内容区：列表 -->
  <div class='main-column'>
    <div class='view-header' style='margin-bottom:16px;'>
      <div>
        <h2>{html.escape(t(lang, 'active_products'))}</h2>
      </div>
    </div>

    <form method='post' action='/bulk-delete' onsubmit='return confirm({json.dumps(t(lang, 'bulk_delete_confirm'))});'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <div class='list-toolbar'>
        <div class='toolbar-left'>
          <label class='checkbox-line' style='margin:0;'>
            <input type='checkbox' onchange='toggleAllCheckboxes(this)' />
            <span>{html.escape(t(lang, 'select_for_bulk_delete'))}</span>
          </label>
        </div>
        <div class='toolbar-right'>
          <span class='text-muted mini'>{html.escape(t(lang, 'running_skip_note'))}</span>
          <button type='submit' class='btn btn-danger'>{html.escape(t(lang, 'bulk_delete'))}</button>
        </div>
      </div>
      {f"<div class='product-list'>{''.join(product_rows)}</div>" if product_rows else f"<div class='empty-state'>{html.escape(t(lang, 'no_products'))}</div>"}
    </form>

    <div class='view-header' style='margin-top: 48px; margin-bottom:16px;'>
      <div>
        <h2>{html.escape(t(lang, 'reusable_claw_profiles'))}</h2>
      </div>
    </div>
    
    <div class='text-muted' style='margin-bottom:16px; font-size: 0.95rem; max-width: 800px;'>
      {html.escape(t(lang, 'claw_identity_body'))}
    </div>
    <div style='display:grid; gap:16px;'>{profiles_html}</div>
  </div>

  <!-- 右侧/辅助操作区：创建表单 -->
  <div class='sticky-panel'>
    <div class='card sidebar-card'>
      <div class='card-header'><div class='card-title'>✦ {html.escape(t(lang, 'create_product'))}</div></div>
      <div class='card-body'>
        <form method='post' action='/create'>
          <input type='hidden' name='lang' value='{html.escape(lang)}' />

          <label>{html.escape(t(lang, 'product_name'))}</label>
          <input name='name' placeholder='e.g. My Awesome App' />

          <label>{html.escape(t(lang, 'goal'))}</label>
          <textarea name='goal' rows='3' placeholder='{html.escape(t(lang, 'goal_placeholder'))}'></textarea>

          <label>{html.escape(t(lang, 'product_folder'))}</label>
          <input name='productFolder' value='/mnt/c/claw/codex测试' />

          <div class='settings-group'>
            <div class='settings-group-title'>{html.escape(t(lang, 'claw_setting'))}</div>
            <label>{html.escape(t(lang, 'claw_profile_select'))}</label>
            <select name='clawProfileId'>{profile_options}</select>

            <div class='form-row'>
              <div>
                <label>{html.escape(t(lang, 'claw_endpoint'))}</label>
                <input name='clawEndpoint' value='http://localhost:8317/v1' />
              </div>
              <div>
                <label>{html.escape(t(lang, 'claw_api_key'))}</label>
                <input type='password' name='clawApiKey' value='' />
              </div>
            </div>

            <div class='form-row'>
              <div>
                <label>{html.escape(t(lang, 'claw_model'))}</label>
                <input name='clawModel' placeholder='{html.escape(default_profile.get('model', ''))}' />
              </div>
              <div>
                <label>{html.escape(t(lang, 'claw_thinking'))}</label>
                <input name='clawThinking' placeholder='{html.escape(default_profile.get('thinking', ''))}' />
              </div>
            </div>

            <label>{html.escape(t(lang, 'claw_soul'))}</label>
            <textarea name='clawSoul' rows='3' placeholder='{html.escape(t(lang, 'profile_soul_placeholder'))}'></textarea>

            <label>{html.escape(t(lang, 'claw_skills'))}</label>
            <textarea name='clawSkills' rows='3' placeholder='{html.escape(t(lang, 'profile_skills_placeholder'))}'></textarea>
          </div>

          <div class='settings-group' style='margin-bottom:24px;'>
            <div class='settings-group-title'>{html.escape(t(lang, 'codex_setting'))}</div>
            <div class='form-row'>
              <div>
                <label>{html.escape(t(lang, 'codex_endpoint'))}</label>
                <input name='codexEndpoint' value='http://localhost:8317/v1' />
              </div>
              <div>
                <label>{html.escape(t(lang, 'codex_api_key'))}</label>
                <input type='password' name='codexApiKey' value='' />
              </div>
            </div>

            <div class='form-row'>
              <div>
                <label>{html.escape(t(lang, 'codex_model'))}</label>
                <input name='codexModel' value='gpt-5.4-medium' />
              </div>
              <div>
                <label>{html.escape(t(lang, 'codex_thinking'))}</label>
                <input name='codexThinking' value='medium' />
              </div>
            </div>

            <label class='checkbox-line'>
              <input type='checkbox' name='codexPlanMode' checked />
              <span>{html.escape(t(lang, 'enable_plan'))}</span>
            </label>
            <label class='checkbox-line' style='margin-bottom:0;'>
              <input type='checkbox' name='codexMaxPermission' checked />
              <span>{html.escape(t(lang, 'enable_max_permission'))}</span>
            </label>
          </div>

          <button type='submit' class='btn btn-primary' style='width:100%; height: 44px; font-size: 1rem;'>{html.escape(t(lang, 'create_button'))}</button>
        </form>
      </div>
    </div>

    <div class='card sidebar-card'>
      <div class='card-header'><div class='card-title'>+ {html.escape(t(lang, 'create_profile'))}</div></div>
      <div class='card-body'>
        <form method='post' action='/profiles/create'>
          <input type='hidden' name='lang' value='{html.escape(lang)}' />
          <label>{html.escape(t(lang, 'profile_name'))}</label>
          <input name='profileName' placeholder='e.g. Sandrone Network Auditor' />

          <label>{html.escape(t(lang, 'profile_description'))}</label>
          <input name='profileDescription' placeholder='{html.escape(t(lang, 'profile_desc_placeholder'))}' />

          <div class='form-row'>
            <div>
              <label>{html.escape(t(lang, 'profile_model_hint'))}</label>
              <input name='profileModel' value='{html.escape(default_profile.get('model', ''))}' />
            </div>
            <div>
              <label>{html.escape(t(lang, 'profile_thinking_hint'))}</label>
              <input name='profileThinking' value='{html.escape(default_profile.get('thinking', ''))}' />
            </div>
          </div>

          <label>{html.escape(t(lang, 'claw_soul'))}</label>
          <textarea name='profileSoul' rows='3'>{html.escape(default_profile.get('soul', ''))}</textarea>

          <label>{html.escape(t(lang, 'claw_skills'))}</label>
          <textarea name='profileSkills' rows='3'>{html.escape(default_profile.get('skills', ''))}</textarea>

          <button type='submit' class='btn btn-secondary' style='width:100%; height: 44px;'>{html.escape(t(lang, 'create_profile_button'))}</button>
        </form>
      </div>
    </div>
  </div>
</div>
"""
        self.send_html(page_template(t(lang, 'app_title'), body, lang, '/'))

    def render_product(self, pid: str, lang: str):
        d = product_dir(pid)
        cfg = load_product_config(pid)
        st = load_product_state(pid)
        claw_eff = effective_claw_config(cfg)
        claw_log = html.escape((d / 'logs' / 'claw.log').read_text(encoding='utf-8') if (d / 'logs' / 'claw.log').exists() else t(lang, 'no_logs'))
        codex_log = html.escape((d / 'logs' / 'codex.log').read_text(encoding='utf-8') if (d / 'logs' / 'codex.log').exists() else t(lang, 'no_logs'))
        self_test = st.get('selfTest', {})
        checks = self_test.get('checks', {})
        user_claw = st.get('conversations', {}).get('userClaw', [])[-30:]
        claw_codex = st.get('conversations', {}).get('clawCodex', [])[-30:]
        user_claw_html = render_dialogue(user_claw, t(lang, 'no_user_claw'))
        claw_codex_html = render_dialogue(claw_codex, t(lang, 'no_claw_codex'))

        def badge_class(status: str) -> str:
            if status == 'running':
                return 'badge-running'
            if status in {'delivered', 'passed'}:
                return 'badge-delivered'
            if status == 'failed':
                return 'badge-failed'
            if status == 'stopped':
                return 'badge-stopped'
            return 'badge-idle'

        checks_html = ''.join(
            f"<tr><td><div style='font-weight:700;'>{html.escape(k)}</div></td><td><span class='badge {'badge-delivered' if v.get('ok') else 'badge-failed'}'>{'Pass' if v.get('ok') else 'Fail'}</span></td><td class='mono text-muted'>{html.escape(str(v.get('detail', '')))}</td></tr>"
            for k, v in checks.items()
        ) or f"<tr><td colspan='3' class='text-muted' style='text-align:center;'>{html.escape(t(lang, 'not_run'))}</td></tr>"

        status = st.get('status', 'idle')
        st_status = self_test.get('status', 'not-run')
        is_running = status == 'running' and bool(active_run_info(pid))
        profile = load_claw_profile(claw_eff.get('profileId'))

        body = f"""
<a href='/?lang={lang}' class='back-link'>
  <svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><line x1='19' y1='12' x2='5' y2='12'></line><polyline points='12 19 5 12 12 5'></polyline></svg>
  {html.escape(t(lang, 'back'))}
</a>

<div class='view-header'>
  <div>
    <h1>
      {html.escape(cfg.get('name', t(lang, 'untitled')))}
      <span class='badge {badge_class(status)}'>{html.escape(t(lang, status) if status in I18N[lang] else status)}</span>
      <span class='badge {badge_class(st_status)}'>{html.escape(t(lang, 'self_test'))}: {html.escape(t(lang, st_status) if st_status in I18N[lang] else st_status)}</span>
    </h1>
    <div class='page-subtitle mono'>ID: {html.escape(pid)} · Dir: {html.escape(cfg.get('productFolder', ''))}</div>
  </div>

  <div class='view-header-actions'>
    <form method='post' action='/selftest/{html.escape(pid)}' style='margin:0;'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='btn btn-secondary'>{html.escape(t(lang, 'run_self_test'))}</button>
    </form>
    <form method='post' action='/start/{html.escape(pid)}' style='margin:0;'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='btn btn-primary' {'disabled' if is_running else ''}>{html.escape(t(lang, 'start_continue_run'))}</button>
    </form>
    <form method='post' action='/stop/{html.escape(pid)}' style='margin:0;'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='btn btn-secondary' {'disabled' if not is_running else ''}>{html.escape(t(lang, 'stop_run'))}</button>
    </form>
    <form method='post' action='/delete/{html.escape(pid)}' style='margin:0;' onsubmit='return confirm({json.dumps(t(lang, 'delete_confirm'))});'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='btn btn-danger btn-icon' {'disabled' if is_running else ''}>🗑</button>
    </form>
  </div>
</div>

<div class='card' style='margin-bottom:24px;'>
  <div class='card-header'><div class='card-title'>{html.escape(t(lang, 'configuration_details'))}</div></div>
  <div class='card-body'>
    <div class='three-col'>
      <div>
        <div class='settings-group-title'>{html.escape(t(lang, 'goal'))}</div>
        <div class='settings-group' style='margin-bottom:0; overflow-wrap:break-word;'>{html.escape(cfg.get('goal', ''))}</div>
      </div>
      <div class='settings-group' style='margin-bottom:0;'>
        <div class='settings-group-title'>{html.escape(t(lang, 'claw_setting'))}</div>
        <div style='font-size:0.93rem; line-height:1.8;'>
          <b>{html.escape(t(lang, 'profile_label'))}:</b> {html.escape(claw_eff.get('profileName', ''))}<br/>
          <b>{html.escape(t(lang, 'model'))}:</b> {html.escape(claw_eff.get('model', ''))} <span class='text-muted'>({html.escape(claw_eff.get('thinking', ''))})</span><br/>
          <b>{html.escape(t(lang, 'api_key_present'))}:</b> <span class='badge badge-delivered'>{html.escape(t(lang, mask_present(claw_eff.get('apiKey'))))}</span><br/>
          <b>Endpoint:</b> <span class='mono text-muted'>{html.escape(claw_eff.get('endpoint', ''))}</span>
        </div>
      </div>
      <div class='settings-group' style='margin-bottom:0;'>
        <div class='settings-group-title'>{html.escape(t(lang, 'codex_setting'))}</div>
        <div style='font-size:0.93rem; line-height:1.8;'>
          <b>{html.escape(t(lang, 'model'))}:</b> {html.escape(cfg.get('codex', {}).get('model', ''))} <span class='text-muted'>({html.escape(cfg.get('codex', {}).get('thinking', ''))})</span><br/>
          <b>{html.escape(t(lang, 'api_key_present'))}:</b> <span class='badge badge-delivered'>{html.escape(t(lang, mask_present(cfg.get('codex', {}).get('apiKey'))))}</span><br/>
          <b>Endpoint:</b> <span class='mono text-muted'>{html.escape(cfg.get('codex', {}).get('endpoint', ''))}</span><br/>
          <div style='margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;'>
            <span class='badge badge-idle'>Plan: {cfg.get('codex', {}).get('planMode')}</span>
            <span class='badge badge-idle'>MaxPerm: {cfg.get('codex', {}).get('maxPermission')}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class='two-col' style='margin-bottom:24px;'>
  <div class='card' style='margin:0;'>
    <div class='card-header'><div class='card-title'>{html.escape(t(lang, 'role_policy_title'))}</div></div>
    <div class='card-body text-muted'>{html.escape(t(lang, 'role_policy_body'))}</div>
  </div>
  <div class='card' style='margin:0;'>
    <div class='card-header'><div class='card-title'>{html.escape(t(lang, 'effective_claw_identity'))}</div></div>
    <div class='card-body'>
      <div class='text-muted' style='margin-bottom:12px;'>{html.escape(profile.get('description', ''))}</div>
      <div style='margin-bottom:8px;'><b>{html.escape(t(lang, 'profile_label'))}:</b> {html.escape(claw_eff.get('profileName', ''))}</div>
      <div style='margin-bottom:4px;'><b>{html.escape(t(lang, 'soul_label'))}:</b></div>
      <div class='mono settings-group' style='font-size:0.85rem;'>{html.escape(claw_eff.get('soul', ''))}</div>
      <div style='margin-bottom:4px;'><b>{html.escape(t(lang, 'skills_label'))}:</b></div>
      <div class='mono settings-group' style='font-size:0.85rem; margin-bottom:0;'>{html.escape(claw_eff.get('skills', ''))}</div>
    </div>
  </div>
</div>

<div class='two-col' style='margin-bottom:24px;'>
  <div class='card' style='margin:0;'>
    <div class='card-header'><div class='card-title'>{html.escape(t(lang, 'user_claw_dialogue'))}</div></div>
    <div class='dialogue-shell'>{user_claw_html}</div>
    <div class='card-body' style='border-top:1px solid var(--border); border-radius: 0 0 var(--radius) var(--radius);'>
      <form method='post' action='/append-user/{html.escape(pid)}' style='margin:0;'>
        <input type='hidden' name='lang' value='{html.escape(lang)}' />
        <textarea name='message' rows='3' placeholder='{html.escape(t(lang, 'append_placeholder'))}' required></textarea>
        <div style='display:flex; justify-content:flex-end;'>
          <button type='submit' class='btn btn-primary'>{html.escape(t(lang, 'append_button'))}</button>
        </div>
      </form>
    </div>
  </div>

  <div class='card' style='margin:0;'>
    <div class='card-header'><div class='card-title'>{html.escape(t(lang, 'claw_codex_dialogue'))}</div></div>
    <div class='dialogue-shell' style='border-radius: 0 0 var(--radius) var(--radius);'>{claw_codex_html}</div>
  </div>
</div>

<div class='two-col' style='margin-bottom:24px;'>
  <div class='card' style='margin:0;'>
    <div class='card-header'><div class='card-title'>{html.escape(t(lang, 'save_current_claw_profile'))}</div></div>
    <div class='card-body'>
      <div class='text-muted' style='margin-bottom:16px;'>{html.escape(t(lang, 'profile_saved_hint'))}</div>
      <form method='post' action='/save-profile/{html.escape(pid)}'>
        <input type='hidden' name='lang' value='{html.escape(lang)}' />
        <label>{html.escape(t(lang, 'profile_name'))}</label>
        <input name='profileName' placeholder='{html.escape(claw_eff.get('profileName', ''))}' />
        <label>{html.escape(t(lang, 'profile_description'))}</label>
        <input name='profileDescription' placeholder='{html.escape(t(lang, 'profile_desc_placeholder'))}' />
        <button type='submit' class='btn btn-secondary'>{html.escape(t(lang, 'save_profile_button'))}</button>
      </form>
    </div>
  </div>

  <div class='card' style='margin:0;'>
    <div class='card-header'>
      <div class='card-title'>{html.escape(t(lang, 'self_test_details'))}</div>
      <span class='badge {badge_class(st_status)}'>{html.escape(t(lang, st_status) if st_status in I18N[lang] else st_status)}</span>
    </div>
    <div class='card-body' style='padding:0;'>
      <table class='data-table'>
        <thead>
          <tr>
            <th>{html.escape(t(lang, 'check'))}</th>
            <th>{html.escape(t(lang, 'result'))}</th>
            <th>{html.escape(t(lang, 'detail'))}</th>
          </tr>
        </thead>
        <tbody>{checks_html}</tbody>
      </table>
      <div class='card-body' style='border-top:1px solid var(--border);'>
        <form method='post' action='/selftest/{html.escape(pid)}' style='margin:0;'>
          <input type='hidden' name='lang' value='{html.escape(lang)}' />
          <button type='submit' class='btn btn-secondary'>{html.escape(t(lang, 'run_self_test'))}</button>
        </form>
      </div>
    </div>
  </div>
</div>

<div class='two-col'>
  <div class='terminal-window'>
    <div class='terminal-header'>
      <div class='terminal-dot dot-r'></div><div class='terminal-dot dot-y'></div><div class='terminal-dot dot-g'></div>
      <span class='mono text-muted' style='margin-left:8px;'>~/{html.escape(t(lang, 'claw_log'))}</span>
    </div>
    <div class='terminal-body mono'>{claw_log}</div>
  </div>

  <div class='terminal-window'>
    <div class='terminal-header'>
      <div class='terminal-dot dot-r'></div><div class='terminal-dot dot-y'></div><div class='terminal-dot dot-g'></div>
      <span class='mono text-muted' style='margin-left:8px;'>~/{html.escape(t(lang, 'codex_log'))}</span>
    </div>
    <div class='terminal-body mono'>{codex_log}</div>
  </div>
</div>

<script>setTimeout(() => location.reload(), 5000)</script>
"""
        self.send_html(page_template(cfg.get('name', pid), body, lang, f'/product/{pid}'))

    def send_html(self, body: bytes):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, obj):
        body = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location: str):
        safe_location = quote(location, safe='/:?=&-_.~')
        self.send_response(303)
        self.send_header('Location', safe_location)
        self.end_headers()

    def log_message(self, fmt, *args):
        return


def main():
    ensure_default_profile()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f'Listening on http://{HOST}:{PORT}')
    httpd.serve_forever()


if __name__ == '__main__':
    main()