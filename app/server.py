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

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PRODUCTS = DATA / 'products'
TRASH = DATA / 'trash'
CLAW_PROFILES = DATA / 'claw-profiles'
RUNS = ROOT / 'runs'
DEFAULT_ACPX = '/home/a/.openclaw/extensions/acpx/node_modules/.bin/acpx'
ACPX = Path(os.environ.get('ACPX_BIN', DEFAULT_ACPX))

HOST = os.environ.get('PRODUCTS_UI_HOST', '127.0.0.1')
PORT = int(os.environ.get('PRODUCTS_UI_PORT', '8765'))
DEFAULT_LANG = os.environ.get('PRODUCTS_UI_DEFAULT_LANG', 'en')
DEFAULT_AGENT_ENDPOINT = os.environ.get('PRODUCTS_UI_DEFAULT_OPENAI_BASE_URL', 'http://localhost:8317/v1')
DEFAULT_CODEX_ENDPOINT = os.environ.get('PRODUCTS_UI_DEFAULT_CODEX_BASE_URL', 'https://www.right.codes/codex/v1')
DEFAULT_CODEX_API_KEY = os.environ.get('PRODUCTS_UI_DEFAULT_CODEX_API_KEY', '')
DEFAULT_PRODUCT_FOLDER = os.environ.get('PRODUCTS_UI_DEFAULT_PRODUCT_FOLDER', str(ROOT / 'workspace'))
DEFAULT_PROXY = os.environ.get('PRODUCTS_UI_PROXY', '').strip()
DEFAULT_NO_PROXY = os.environ.get('PRODUCTS_UI_NO_PROXY', '127.0.0.1,localhost,::1').strip()
DEFAULT_PROFILE_ID = 'sandrone-default'

for p in [PRODUCTS, TRASH, CLAW_PROFILES, RUNS]:
    p.mkdir(parents=True, exist_ok=True)

ACTIVE_RUNS: dict[str, dict] = {}
ACTIVE_SELF_TESTS: dict[str, dict] = {}
RUN_LOCK = threading.Lock()
SELF_TEST_LOCK = threading.Lock()

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
        'max_turns': '最大回合数',
        'max_turns_help': '每次运行最多执行多少个回合；达到上限会标记失败（默认 8）。',
        'turn_progress': '回合进度',
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
        'back': '返回控制台',
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
        'bulk_delete': '批量删除',
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
        'claw_log': 'Agent Log',
        'codex_log': 'Codex Log',
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
        'claw_identity_title': '当前生效的 Agent 身份',
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
        'max_turns': 'Max Turns',
        'max_turns_help': 'Max Claw↔Codex turns per run; reaching the limit will mark failed (default 8).',
        'turn_progress': 'Turn progress',
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
        'back': 'Back to Dashboard',
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
        'bulk_delete': 'Bulk Delete',
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


def normalize_product_identity(raw_name: str, raw_folder: str) -> tuple[str, str, bool]:
    name = (raw_name or '').strip()
    folder = (raw_folder or '').strip()
    inferred_from_name_path = False

    default_folder = str(Path(DEFAULT_PRODUCT_FOLDER).expanduser())
    folder = str(Path(folder).expanduser()) if folder else ''

    looks_like_path = bool(name) and (
        name.startswith('/')
        or name.startswith('~')
        or name.startswith('./')
        or name.startswith('../')
        or bool(re.match(r'^[A-Za-z]:[\\/]', name))
    )

    if looks_like_path and (not folder or folder == default_folder):
        p = Path(name).expanduser()
        folder = str(p)
        if p.name.strip():
            name = p.name.strip()
        inferred_from_name_path = True

    if not name:
        name = 'Untitled Product'
    if not folder:
        folder = default_folder

    return name, folder, inferred_from_name_path


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
    if 'maxTurns' not in cfg:
        cfg['maxTurns'] = 8
        changed = True
    else:
        try:
            cfg['maxTurns'] = int(cfg.get('maxTurns') or 8)
        except Exception:
            cfg['maxTurns'] = 8
        if cfg['maxTurns'] < 1:
            cfg['maxTurns'] = 1
        if cfg['maxTurns'] > 99:
            cfg['maxTurns'] = 99
    claw = cfg.setdefault('claw', {})
    codex = cfg.setdefault('codex', {})
    defaults = {
        'endpoint': DEFAULT_AGENT_ENDPOINT,
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
        'endpoint': DEFAULT_CODEX_ENDPOINT,
        'apiKey': DEFAULT_CODEX_API_KEY,
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
        'currentTurn': 0,
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
    name, product_folder, inferred_from_name_path = normalize_product_identity(
        form.get('name', ''),
        form.get('productFolder', ''),
    )
    try:
        max_turns = int((form.get('maxTurns') or '').strip() or '8')
    except Exception:
        max_turns = 8
    if max_turns < 1:
        max_turns = 1
    if max_turns > 99:
        max_turns = 99
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
        'productFolder': product_folder,
        'maxTurns': max_turns,
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
            'endpoint': form.get('codexEndpoint', '').strip() or DEFAULT_CODEX_ENDPOINT,
            'apiKey': form.get('codexApiKey', '').strip() or DEFAULT_CODEX_API_KEY,
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
    if inferred_from_name_path:
        append_log(d / 'logs' / 'claw.log', f'[{now_iso()}] Interpreted product name as a filesystem path and normalized to name={name!r}, productFolder={product_folder!r}.')
    append_user_claw_message(product_id, 'claw', f"Agent profile '{profile.get('name')}' attached to this product. Ready for user instructions.")
    return product_id


def build_codex_env(cfg: dict) -> dict:
    codex = cfg.get('codex', {})
    env = os.environ.copy()
    if codex.get('endpoint'):
        env['OPENAI_BASE_URL'] = codex['endpoint']
    if codex.get('apiKey'):
        env['OPENAI_API_KEY'] = codex['apiKey']

    lower_proxy = env.get('http_proxy') or env.get('https_proxy') or ''
    upper_proxy = env.get('HTTP_PROXY') or env.get('HTTPS_PROXY') or ''
    effective_proxy = DEFAULT_PROXY or lower_proxy or upper_proxy
    if not DEFAULT_PROXY and lower_proxy and upper_proxy and lower_proxy != upper_proxy:
        effective_proxy = lower_proxy

    if effective_proxy:
        env['HTTP_PROXY'] = effective_proxy
        env['HTTPS_PROXY'] = effective_proxy
        env['http_proxy'] = effective_proxy
        env['https_proxy'] = effective_proxy
    else:
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            env.pop(key, None)

    effective_no_proxy = DEFAULT_NO_PROXY or env.get('no_proxy') or env.get('NO_PROXY') or '127.0.0.1,localhost,::1'
    env['NO_PROXY'] = effective_no_proxy
    env['no_proxy'] = effective_no_proxy
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


def active_self_test_info(product_id: str):
    with SELF_TEST_LOCK:
        return ACTIVE_SELF_TESTS.get(product_id)


def set_active_self_test(product_id: str, info: dict):
    with SELF_TEST_LOCK:
        ACTIVE_SELF_TESTS[product_id] = info


def clear_active_self_test(product_id: str):
    with SELF_TEST_LOCK:
        ACTIVE_SELF_TESTS.pop(product_id, None)


def terminate_process_tree(proc, grace_seconds: float = 5.0):
    if not proc:
        return
    try:
        if proc.poll() is not None:
            return
    except Exception:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    deadline = time.time() + grace_seconds
    while time.time() < deadline:
        try:
            if proc.poll() is not None:
                return
        except Exception:
            return
        time.sleep(0.1)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def start_run(product_id: str) -> str:
    info = active_run_info(product_id)
    if info and info.get('thread') and info['thread'].is_alive():
        return info.get('run_id') or 'running'

    st = load_product_state(product_id)
    run_id = datetime.now().strftime('%Y%m%d-%H%M%S')
    stop_event = threading.Event()
    st.update({'status': 'running', 'updatedAt': now_iso(), 'lastRunId': run_id, 'lastError': None, 'stopRequested': False, 'currentTurn': 0})
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


def start_self_test(product_id: str) -> str:
    info = active_self_test_info(product_id)
    if info and info.get('thread') and info['thread'].is_alive():
        return 'already-running'

    st = load_product_state(product_id)
    st.setdefault('selfTest', {})
    st['selfTest'] = {'status': 'running', 'updatedAt': now_iso(), 'checks': {}}
    st['updatedAt'] = now_iso()
    save_product_state(product_id, st)

    t_runner = threading.Thread(target=run_self_test, args=(product_id,), daemon=True)
    set_active_self_test(product_id, {'thread': t_runner, 'procs': [], 'startedAt': now_iso()})
    t_runner.start()
    return 'started'


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
    claw_log = d / 'logs' / 'claw.log'
    codex_log = d / 'logs' / 'codex.log'
    product_folder = cfg.get('productFolder') or '/tmp'
    codex = cfg.get('codex', {})
    claw_eff = effective_claw_config(cfg)
    session_name = codex.get('sessionName') or f'oc-product-{product_id}'
    env = build_codex_env(cfg)
    checks = {}

    def log_claw(text: str):
        append_log(claw_log, f'[{now_iso()}] {text}')

    def log_codex(text: str):
        append_log(codex_log, f'[{now_iso()}] {text}')

    def record_self_test(final_status: str):
        st = load_product_state(product_id)
        st['selfTest'] = {'status': final_status, 'updatedAt': now_iso(), 'checks': checks}
        st['updatedAt'] = now_iso()
        save_product_state(product_id, st)

    def run_selftest_command(cmd: list[str], timeout_seconds: int) -> tuple[int | None, str, bool]:
        proc = None
        try:
            proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            info = active_self_test_info(product_id)
            if info is not None:
                info.setdefault('procs', []).append(proc)
            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
                out = (stdout or '') + (('\n' + stderr) if stderr else '')
                return proc.returncode, out, False
            except subprocess.TimeoutExpired:
                terminate_process_tree(proc)
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                except Exception:
                    stdout, stderr = '', ''
                out = (stdout or '') + (('\n' + stderr) if stderr else '')
                return None, out, True
        finally:
            if proc is not None:
                info = active_self_test_info(product_id)
                if info is not None:
                    info['procs'] = [p for p in info.get('procs', []) if p is not proc]

    try:
        log_claw('Starting self-test.')

        checks['agent_config'] = {
            'ok': bool(claw_eff.get('endpoint') and claw_eff.get('model')),
            'detail': f"profile={claw_eff.get('profileName','-')} endpoint={claw_eff.get('endpoint','-')} model={claw_eff.get('model','-')} thinking={claw_eff.get('thinking','-')} apiKey={'yes' if claw_eff.get('apiKey') else 'no'}",
        }
        log_claw(f"Self-test agent_config: {checks['agent_config']}")

        checks['agent_connection'] = probe_openai_like_endpoint(claw_eff.get('endpoint', ''), claw_eff.get('apiKey'))
        log_claw(f"Self-test agent_connection: {checks['agent_connection']['ok']}")

        checks['product_folder'] = {'ok': Path(product_folder).exists(), 'detail': product_folder}
        log_claw(f"Self-test product_folder: {checks['product_folder']}")

        session_cmd = [str(ACPX), '--cwd', product_folder, 'codex', 'sessions', 'ensure', '--name', session_name]
        rc, out, timed_out = run_selftest_command(session_cmd, 45)
        log_codex(out)
        if timed_out:
            checks['codex_session'] = {'ok': False, 'detail': f'timed out after 45 seconds: {" ".join(session_cmd)}'}
        else:
            checks['codex_session'] = {'ok': rc == 0, 'detail': out[-500:]}
        log_claw(f"Self-test codex_session: {checks['codex_session']['ok']}")

        status_cmd = [str(ACPX), '--cwd', product_folder, 'codex', 'status', '--session', session_name]
        rc, out, timed_out = run_selftest_command(status_cmd, 20)
        log_codex(out)
        if timed_out:
            checks['codex_status'] = {'ok': False, 'detail': f'timed out after 20 seconds: {" ".join(status_cmd)}'}
        else:
            detail = out[-500:]
            if rc == 0 and 'status:' in out and 'status: no-session' not in out:
                checks['codex_status'] = {'ok': True, 'detail': detail}
            elif 'status: dead' in out:
                checks['codex_status'] = {'ok': True, 'detail': detail + '\n(note: session process is dead, but this backend may still support one-shot exec successfully)'}
            else:
                checks['codex_status'] = {'ok': False, 'detail': detail}
        log_claw(f"Self-test codex_status: {checks['codex_status']['ok']}")

        prompt_cmd = [str(ACPX), '--cwd', product_folder, '--approve-all', '--non-interactive-permissions', 'deny', 'codex', 'exec', 'Reply with exactly SELFTEST_CODEX_OK']
        rc, out, timed_out = run_selftest_command(prompt_cmd, 60)
        log_codex(out)
        if timed_out:
            checks['codex_prompt'] = {'ok': False, 'detail': f'timed out after 60 seconds: {" ".join(prompt_cmd)}'}
        else:
            checks['codex_prompt'] = {'ok': rc == 0 and 'SELFTEST_CODEX_OK' in out, 'detail': out[-500:]}
        log_claw(f"Self-test codex_prompt: {checks['codex_prompt']['ok']}")

        overall = checks['agent_config']['ok'] and checks['agent_connection']['ok'] and checks['product_folder']['ok'] and checks['codex_session']['ok'] and checks['codex_prompt']['ok']
        record_self_test('passed' if overall else 'failed')
        append_user_claw_message(product_id, 'claw', f"Self-test finished: {'passed' if overall else 'failed'}.")
        log_claw(f"Self-test finished: {'passed' if overall else 'failed'}.")
    except Exception as e:
        checks['internal_error'] = {'ok': False, 'detail': str(e)}
        record_self_test('failed')
        append_user_claw_message(product_id, 'claw', 'Self-test finished: failed.')
        log_claw(f'Self-test failed with exception: {e}')
    finally:
        info = active_self_test_info(product_id)
        if info is not None:
            for proc in info.get('procs', []):
                terminate_process_tree(proc)
        clear_active_self_test(product_id)


def run_codex_command(
    cmd: list[str],
    env: dict,
    timeout_seconds: int | None,
    stop_event: threading.Event,
    product_id: str,
    progress_probe=None,
    on_stdout_line=None,
    on_stderr_line=None,
    idle_grace_seconds: int = 1800,
    hard_deadlock_seconds: int | None = 43200,
    poll_seconds: float = 2.0,
):
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True, bufsize=1)
    set_active_proc(product_id, proc)
    start = time.time()
    activity = {'stdout': start, 'stderr': start}
    io_lock = threading.Lock()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def reader(stream, chunks: list[str], key: str):
        try:
            while True:
                line = stream.readline()
                if line == '':
                    break
                with io_lock:
                    chunks.append(line)
                    activity[key] = time.time()
                try:
                    if key == 'stdout' and on_stdout_line is not None:
                        on_stdout_line(line)
                    if key == 'stderr' and on_stderr_line is not None:
                        on_stderr_line(line)
                except Exception:
                    pass
        except Exception as e:
            with io_lock:
                chunks.append(f'\n[taskcaptain {key} reader error] {e}\n')
                activity[key] = time.time()

    t_out = threading.Thread(target=reader, args=(proc.stdout, stdout_chunks, 'stdout'), daemon=True)
    t_err = threading.Thread(target=reader, args=(proc.stderr, stderr_chunks, 'stderr'), daemon=True)
    t_out.start()
    t_err.start()

    def combined_output() -> str:
        with io_lock:
            stdout = ''.join(stdout_chunks)
            stderr = ''.join(stderr_chunks)
        return stdout + (("\n" + stderr) if stderr else '')

    last_probe_value = None
    last_probe_at = start
    if progress_probe is not None:
        try:
            last_probe_value = progress_probe()
        except Exception as e:
            last_probe_value = {'probeError': str(e)}

    while True:
        if stop_event.is_set():
            terminate_process_tree(proc)
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            return -15, combined_output(), True

        now = time.time()
        if progress_probe is not None:
            try:
                probe_value = progress_probe()
            except Exception as e:
                probe_value = {'probeError': str(e)}
            if probe_value != last_probe_value:
                last_probe_value = probe_value
                last_probe_at = now

        if proc.poll() is not None:
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            return proc.returncode, combined_output(), False

        if timeout_seconds is not None and now - start > timeout_seconds:
            terminate_process_tree(proc)
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            return 124, combined_output(), False

        last_activity_at = max(last_probe_at, activity['stdout'], activity['stderr'])
        if idle_grace_seconds and now - last_activity_at > idle_grace_seconds:
            terminate_process_tree(proc)
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            out = combined_output()
            out += f"\n[taskcaptain] terminated after {int(now - last_activity_at)}s with no progress evidence."
            return 124, out, False

        if hard_deadlock_seconds is not None and now - start > hard_deadlock_seconds:
            terminate_process_tree(proc)
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            out = combined_output()
            out += f"\n[taskcaptain] terminated after absolute deadlock guard of {int(hard_deadlock_seconds)}s."
            return 124, out, False

        time.sleep(poll_seconds)


def summarize_user_claw_messages(st: dict, limit: int = 8) -> str:
    user_msgs = [x.get('text', '') for x in st.get('conversations', {}).get('userClaw', []) if x.get('role') == 'user']
    return '\n'.join(f'- {x}' for x in user_msgs[-limit:]) or '- none'



def extract_terminal_token(text: str) -> str | None:
    matches = re.findall(r'(?m)^(DELIVERED_OK|FAILED_FINAL|NEEDS_MORE_WORK)\s*$', text or '')
    return matches[-1] if matches else None


def extract_json_object(text: str) -> dict | None:
    raw = (text or '').strip()
    if not raw:
        return None
    fenced = re.match(r'^```(?:json)?\s*(.*?)\s*```$', raw, re.S)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    decoder = json.JSONDecoder()
    for i, ch in enumerate(raw):
        if ch != '{':
            continue
        try:
            obj, _ = decoder.raw_decode(raw[i:])
        except Exception:
            continue
        if isinstance(obj, dict):
            return obj
    return None



def stringify_for_log(value) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        try:
            return str(value)
        except Exception:
            return ''


def build_chat_completions_url(base: str) -> str:
    base = (base or '').rstrip('/')
    if not base:
        return ''
    if base.endswith('/chat/completions'):
        return base
    return f'{base}/chat/completions'


def infer_project_kind(cfg: dict, user_context: str = '') -> str:
    text = ' '.join([
        str(cfg.get('name', '')),
        str(cfg.get('goal', '')),
        str(user_context or ''),
    ]).lower()
    if any(k in text for k in ['算法', 'algorithm', '优化', 'optimization', 'theory', 'theoretical', 'idea', 'proof', 'benchmark', '性能', '复杂度', '收敛', 'search strategy']):
        return 'algorithm_research'
    if any(k in text for k in ['frontend', '前端', '页面', 'dashboard', 'demo', '界面', '交互', '库存', '订单', '采购', '台']):
        return 'frontend_demo'
    if any(k in text for k in ['api', 'backend', '后端', 'server', '服务', '数据库', '接口']):
        return 'backend_service'
    if any(k in text for k in ['script', 'cli', '命令行', '批处理', 'automation', '工具']):
        return 'script_tool'
    if any(k in text for k in ['文档', 'docs', 'readme', '手册', '教程', 'spec']):
        return 'docs_or_spec'
    return 'general_software'


def project_acceptance_profile(kind: str) -> dict:
    profiles = {
        'frontend_demo': {
            'delivery_bar': [
                'Project structure exists and is non-empty.',
                'There is a documented local startup path.',
                'The main UI renders in Chinese (or the requested language) and is not blank.',
                'Core pages/modules requested by the user are present.',
                'At least one real interaction or workflow is verified.',
                'README includes install/start/demo steps and verification notes.',
            ],
            'stretch_bar': [
                'Browser-level automated acceptance coverage exists.',
                'UI polish and advanced regression checks are present.',
                'Extended data persistence or more advanced UX checks are covered.',
            ],
            'verification_focus': 'Prefer build/start/browser/http verification and key-file inspection. Do not block delivery only because stretch-bar browser automation is missing if delivery-bar evidence is already strong.',
        },
        'backend_service': {
            'delivery_bar': [
                'Service starts locally with documented instructions.',
                'At least one key endpoint or workflow is exercised successfully.',
                'Configuration/README is sufficient for local use.',
                'Core data flow and expected outputs are demonstrated.',
            ],
            'stretch_bar': [
                'Automated test suite coverage is added.',
                'Load/error-handling cases are documented or tested.',
            ],
            'verification_focus': 'Prefer startup logs, HTTP status checks, smoke tests, and configuration correctness.',
        },
        'script_tool': {
            'delivery_bar': [
                'The tool runs locally with a documented command.',
                'Representative input/output behavior is demonstrated.',
                'README explains usage and limitations.',
            ],
            'stretch_bar': [
                'Extra automation, packaging, or edge-case coverage is added.',
            ],
            'verification_focus': 'Prefer CLI execution evidence, deterministic examples, and output inspection.',
        },
        'docs_or_spec': {
            'delivery_bar': [
                'Core requested documents/specs exist and are coherent.',
                'Structure, scope, and examples are sufficient for use.',
            ],
            'stretch_bar': [
                'Extended polish, diagrams, or exhaustive examples are added.',
            ],
            'verification_focus': 'Prefer direct file-content inspection over build/runtime checks.',
        },
        'algorithm_research': {
            'delivery_bar': [
                'The hypothesis/idea is clearly stated.',
                'A concrete method or algorithm design is produced.',
                'There is an evaluation plan or experiment design.',
                'There is at least one implementation artifact, derivation artifact, benchmark artifact, or falsification result.',
                'The result clearly states whether the idea appears promising, inconclusive, or ineffective.',
            ],
            'stretch_bar': [
                'There are broader benchmarks, stronger proofs, more baselines, or more complete ablations.',
                'There is a stronger implementation/performance package beyond the minimum validation needed for the current idea.',
            ],
            'verification_focus': 'Do not treat “not fully proven” as automatic failure. For research/theory work, delivery can be a well-supported negative result, an inconclusive result, a benchmark report, a derivation, or a prototype with evidence. Judge validity of the idea, rigor of reasoning, and whether the current iteration produced meaningful evidence.',
        },
        'general_software': {
            'delivery_bar': [
                'Non-empty project artifacts exist.',
                'There is a documented way to run or inspect the result.',
                'Core requested capability is demonstrated with evidence.',
            ],
            'stretch_bar': [
                'Additional polish, automation, or stronger testing is added.',
            ],
            'verification_focus': 'Prefer pragmatic evidence of use over perfection.',
        },
    }
    return profiles.get(kind, profiles['general_software'])


def openai_chat_completion(base_url: str, api_key: str | None, model: str, messages: list[dict], timeout: int = 120) -> tuple[str, dict]:
    url = build_chat_completions_url(base_url)
    if not url:
        raise RuntimeError('missing chat completions base url')
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    payload = {
        'model': model,
        'messages': messages,
        'stream': False,
    }
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode('utf-8', 'ignore')
    parsed = json.loads(body)
    choices = parsed.get('choices') or []
    if not choices:
        raise RuntimeError(f'no choices in chat completion response: {body[:500]}')
    message = choices[0].get('message') or {}
    content = message.get('content', '')
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    parts.append(item.get('text', ''))
                elif 'text' in item:
                    parts.append(str(item.get('text', '')))
        content = ''.join(parts)
    return str(content or ''), parsed


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
    claw_log = d / 'logs' / 'claw.log'
    codex_log = d / 'logs' / 'codex.log'
    product_folder = cfg.get('productFolder') or '/tmp'
    codex = cfg.get('codex', {})
    claw_eff = effective_claw_config(cfg)
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

    def workspace_snapshot(max_files: int = 120, max_depth: int = 4) -> str:
        root = Path(product_folder)
        if not root.exists():
            return f'(workspace missing) {product_folder}'
        ignore = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.idea', '.pytest_cache', 'dist', 'build'}
        lines = []
        truncated = False
        try:
            for path in sorted(root.rglob('*')):
                try:
                    rel = path.relative_to(root)
                except Exception:
                    continue
                if any(part in ignore for part in rel.parts):
                    continue
                if path.is_dir():
                    continue
                if len(rel.parts) > max_depth:
                    truncated = True
                    continue
                try:
                    size = path.stat().st_size
                except Exception:
                    size = 0
                lines.append(f'- {rel.as_posix()} ({size} bytes)')
                if len(lines) >= max_files:
                    truncated = True
                    break
        except Exception as e:
            return f'(workspace snapshot error: {e})'
        if not lines:
            return '(workspace is empty)'
        if truncated:
            lines.append(f'- … truncated after {len(lines)} entries')
        return '\n'.join(lines)

    def workspace_material_files(max_depth: int = 4) -> list[str]:
        root = Path(product_folder)
        if not root.exists():
            return []
        ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.idea', '.pytest_cache', 'dist', 'build'}
        ignore_names = {'.DS_Store'}
        ignore_prefixes = {'.w', '.probe_', '.tc_'}
        files: list[str] = []
        try:
            for path in sorted(root.rglob('*')):
                try:
                    rel = path.relative_to(root)
                except Exception:
                    continue
                if any(part in ignore_dirs for part in rel.parts):
                    continue
                if path.is_dir():
                    continue
                if len(rel.parts) > max_depth:
                    continue
                name = path.name
                if name in ignore_names:
                    continue
                if any(name.startswith(prefix) for prefix in ignore_prefixes):
                    continue
                files.append(rel.as_posix())
        except Exception:
            return []
        return files

    def build_file_delta(before: list[str], after: list[str]) -> str:
        before_set = set(before)
        after_set = set(after)
        added = sorted(after_set - before_set)
        removed = sorted(before_set - after_set)
        kept = sorted(after_set & before_set)
        lines = []
        if added:
            lines.append('Added files:')
            lines.extend(f'- {x}' for x in added[:40])
        if removed:
            lines.append('Removed files:')
            lines.extend(f'- {x}' for x in removed[:20])
        if kept and not added and not removed:
            lines.append('No material file delta detected.')
        return '\n'.join(lines) if lines else 'No material file delta detected.'

    def workspace_progress_signature() -> dict:
        root = Path(product_folder)
        files = workspace_material_files()
        sample = []
        total_size = 0
        newest_mtime = 0.0
        for rel in files[:80]:
            path = root / rel
            try:
                stat = path.stat()
                total_size += stat.st_size
                newest_mtime = max(newest_mtime, stat.st_mtime)
                sample.append((rel, stat.st_size, int(stat.st_mtime)))
            except Exception:
                sample.append((rel, None, None))
        progress_path = root / '.taskcaptain' / 'progress.json'
        progress_blob = None
        if progress_path.exists():
            try:
                progress_blob = progress_path.read_text(encoding='utf-8', errors='ignore')[:4000]
            except Exception as e:
                progress_blob = f'progress-read-error:{e}'
        return {
            'filesCount': len(files),
            'filesSample': sample,
            'totalSize': total_size,
            'newestMtime': int(newest_mtime) if newest_mtime else 0,
            'progressBlob': progress_blob,
        }

    def default_codex_task(turn: int, files: list[str]) -> str:
        if project_kind == 'algorithm_research':
            if not files:
                return (
                    f"Work on the algorithm/research task '{cfg.get('name')}' inside the current working directory.\n"
                    f"Goal: {cfg.get('goal')}\n"
                    "The workspace is empty. First create concrete research artifacts immediately instead of only discussing ideas.\n"
                    "Create at minimum: README.md plus one or more of: notes.md, experiment_plan.md, benchmark.py, prototype.py, analysis.md.\n"
                    "Your task is to make the idea testable: formalize the hypothesis, define success/failure criteria, add a benchmark or experiment scaffold, and produce an initial implementation/analysis artifact.\n"
                    "A meaningful negative result, inconclusive result, or falsification can still be valuable if clearly supported by evidence.\n"
                    "Reply with a concise summary of CHANGES, VERIFICATION, and REMAINING."
                )
            return (
                f"Continue the algorithm/research task '{cfg.get('name')}' in the current working directory.\n"
                f"Goal: {cfg.get('goal')}\n"
                "Prefer producing stronger evidence over polishing prose: improve the prototype, run benchmarks, tighten reasoning, compare alternatives, or document why the idea does or does not work.\n"
                "Reply with a concise summary of CHANGES, VERIFICATION, and REMAINING blockers."
            )
        if not files:
            return (
                f"Build the smallest runnable demo for '{cfg.get('name')}' inside the current working directory.\n"
                f"Goal: {cfg.get('goal')}\n"
                "The workspace is empty. Your priority is to create real files immediately instead of planning only.\n"
                "Create at minimum: README.md, index.html, app.js, styles.css.\n"
                "Prefer a static implementation with seeded demo data unless a backend is clearly required by the goal.\n"
                "Do one bounded verification command after creating files, then reply with a concise summary of CHANGES, VERIFICATION, and REMAINING."
            )
        return (
            f"Continue implementing '{cfg.get('name')}' in the current working directory.\n"
            f"Goal: {cfg.get('goal')}\n"
            "Read the existing workspace first, then make the highest-value next changes.\n"
            "Run only bounded verification commands.\n"
            "Reply with a concise summary of CHANGES, VERIFICATION, and REMAINING blockers."
        )

    def call_claw_json(stage: str, user_prompt: str, timeout_seconds: int = 120) -> tuple[dict, str]:
        system_prompt = (
            f"You are {claw_eff.get('profileName')}, the product manager, researcher, supervisor, and acceptance lead for TaskCaptain.\n"
            f"Soul: {claw_eff.get('soul')}\n"
            f"Skills: {claw_eff.get('skills')}\n"
            "Your job is to drive an autonomous delivery loop: understand the requirement, inspect evidence, decide what Codex should do next, and decide whether the product is delivered or failed.\n"
            "Codex is the implementation agent. You are not Codex. Do not pretend to have edited files yourself.\n"
            "Be strict and evidence-based. Do not declare delivery unless the workspace and verification evidence justify it.\n"
            "Respond with JSON only, no markdown fences."
        )
        text, _ = openai_chat_completion(
            claw_eff.get('endpoint', ''),
            claw_eff.get('apiKey', ''),
            claw_eff.get('model', '') or DEFAULT_PROFILE_ID,
            [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            timeout=timeout_seconds,
        )
        parsed = extract_json_object(text) or {}
        if not isinstance(parsed, dict):
            parsed = {}
        log_claw(f'Claw {stage} raw output:\n{text}')
        return parsed, text

    try:
        log_claw(f'Starting run {run_id}. Goal: {cfg.get("goal", "")}'.strip())
        log_claw(f"Execution policy: Claw is the product manager / planner / reviewer / acceptance lead; Codex is the implementation executor inside the product folder.")
        append_user_claw_message(product_id, 'claw', f"{claw_eff.get('profileName')} started run {run_id}. I will plan, review, and decide delivery based on evidence while Codex implements.")
        append_claw_codex_message(product_id, 'claw', f"Run {run_id} opened. Claw supervisor identity: {claw_eff.get('profileName')}.")
        log_claw('Using one-shot Codex exec path with Claw-led plan/review loop.')
        if codex.get('maxPermission'):
            log_claw('Using approve-all permission mode for Codex runs.')

        st = load_product_state(product_id)
        user_context = summarize_user_claw_messages(st)
        project_kind = infer_project_kind(cfg, user_context)
        acceptance_profile = project_acceptance_profile(project_kind)
        progress_idle_grace = int(os.environ.get('TASKCAPTAIN_PROGRESS_IDLE_GRACE_SECONDS', '1800'))
        progress_deadlock_guard = int(os.environ.get('TASKCAPTAIN_PROGRESS_DEADLOCK_SECONDS', '43200'))
        progress_poll_seconds = float(os.environ.get('TASKCAPTAIN_PROGRESS_POLL_SECONDS', '2'))
        cmd_prefix = [str(ACPX), '--cwd', product_folder, '--ttl', '30']
        if codex.get('maxPermission'):
            cmd_prefix += ['--approve-all', '--non-interactive-permissions', 'deny']

        initial_snapshot = workspace_snapshot()
        initial_files = workspace_material_files()
        plan_prompt = (
            f"Stage: initial_planning\n"
            f"Project kind: {project_kind}\n"
            f"Product name: {cfg.get('name')}\n"
            f"Goal: {cfg.get('goal')}\n"
            f"User requests so far:\n{user_context}\n\n"
            f"Current workspace snapshot:\n{initial_snapshot}\n\n"
            f"Delivery bar for this project type:\n{json.dumps(acceptance_profile.get('delivery_bar', []), ensure_ascii=False)}\n\n"
            f"Stretch bar for this project type:\n{json.dumps(acceptance_profile.get('stretch_bar', []), ensure_ascii=False)}\n\n"
            f"Verification focus:\n{acceptance_profile.get('verification_focus', '')}\n\n"
            "Return JSON with exactly these fields: decision, summary, phased_plan, acceptance_checks, codex_task, failure_reason.\n"
            "- decision must be one of: delegate, deliver, fail\n"
            "- phased_plan: list of short stage bullets\n"
            "- acceptance_checks: list of concrete checks focused on the delivery bar first\n"
            "- codex_task: the exact next implementation brief for Codex if decision=delegate\n"
            "- do not treat stretch-bar items as mandatory blockers when delivery-bar evidence can already justify delivery\n"
            "If the workspace is effectively empty, codex_task must force immediate file creation and a minimal runnable scaffold before polish."
        )
        plan, plan_raw = call_claw_json('plan', plan_prompt, timeout_seconds=120)
        plan_decision = (plan.get('decision') or '').strip().lower()
        acceptance_checks = plan.get('acceptance_checks') if isinstance(plan.get('acceptance_checks'), list) else []
        phased_plan = plan.get('phased_plan') if isinstance(plan.get('phased_plan'), list) else []
        if phased_plan:
            append_user_claw_message(product_id, 'claw', 'Claw initial plan:\\n' + '\\n'.join(f'- {x}' for x in phased_plan[:8]))
        if acceptance_checks:
            append_user_claw_message(product_id, 'claw', 'Claw acceptance checks:\\n' + '\\n'.join(f'- {x}' for x in acceptance_checks[:8]))
        if plan_decision == 'deliver':
            set_state(status='delivered', stopRequested=False)
            append_user_claw_message(product_id, 'claw', plan.get('summary') or 'Claw judged the product already delivered at planning stage.')
            return
        if plan_decision == 'fail':
            set_state(status='failed', lastError=plan.get('failure_reason') or 'claw planning failed the task', stopRequested=False)
            append_user_claw_message(product_id, 'claw', plan.get('summary') or 'Claw judged the task should fail at planning stage.')
            return

        current_codex_task = (plan.get('codex_task') or '').strip() or default_codex_task(1, initial_files)
        last_codex_excerpt = ''

        max_turns = 8
        try:
            max_turns = int(cfg.get('maxTurns') or 8)
        except Exception:
            max_turns = 8
        if max_turns < 1:
            max_turns = 1
        if max_turns > 99:
            max_turns = 99

        for turn in range(1, max_turns + 1):
            if stop_event.is_set():
                log_claw('Stop requested before next Codex turn. Marking stopped.')
                append_user_claw_message(product_id, 'claw', f"{claw_eff.get('profileName')} stopped before dispatching the next Codex turn.")
                set_state(status='stopped', stopRequested=True)
                return

            set_state(status='running', stopRequested=False, currentTurn=turn)
            before_files = workspace_material_files()
            before_snapshot = workspace_snapshot()
            codex_dispatch = (
                f"You are Codex, the implementation executor for task '{cfg.get('name')}'.\n"
                f"Goal: {cfg.get('goal')}\n"
                f"Work only inside: {product_folder}\n"
                "Claw is your product manager and acceptance lead. Follow Claw's brief exactly.\n"
                "Do real implementation work in files, not planning-only output.\n"
                "Use bounded verification only; do not start long-lived servers or watchers.\n"
                "Create and maintain a lightweight progress checkpoint at .taskcaptain/progress.json while you work.\n"
                "That checkpoint should contain useful JSON such as current_stage, current_task, changed_files, blockers, and updated_at. Update it whenever you meaningfully progress.\n"
                "If you are thinking for a long time, refresh the progress checkpoint before and after major substeps so the supervisor can distinguish healthy deep work from a stall.\n"
                "At the end, reply with three short sections titled CHANGES, VERIFICATION, and REMAINING.\n\n"
                f"Claw brief for this turn:\n{current_codex_task}\n"
            )
            log_claw(f'Dispatching Codex implementation turn {turn}.')
            append_claw_codex_message(product_id, 'claw', f"Implementation turn {turn}. Claw brief:\n{current_codex_task[:3000]}")
            run_cmd = cmd_prefix + ['codex', 'exec', codex_dispatch]
            rc, out, was_stopped = run_codex_command(
                run_cmd,
                env,
                None,
                stop_event,
                product_id,
                progress_probe=workspace_progress_signature,
                on_stdout_line=lambda line: append_log(codex_log, f'[{now_iso()}] ' + line.rstrip()),
                on_stderr_line=lambda line: append_log(codex_log, f'[{now_iso()}] [stderr] ' + line.rstrip()),
                idle_grace_seconds=progress_idle_grace,
                hard_deadlock_seconds=progress_deadlock_guard,
                poll_seconds=progress_poll_seconds,
            )
            log_codex(f'[taskcaptain] codex exec finished rc={rc} stopped={was_stopped}')
            append_claw_codex_message(product_id, 'codex', out[-3000:])
            append_legacy_codex_conversation(product_id, out[-3000:])
            set_active_proc(product_id, None)
            if out.strip():
                last_codex_excerpt = out[-4000:]

            if was_stopped:
                log_claw('Codex run stopped by user request. Marking stopped.')
                append_user_claw_message(product_id, 'claw', f"{claw_eff.get('profileName')} confirmed the Codex run was stopped by user request.")
                set_state(status='stopped', stopRequested=True)
                return

            after_files = workspace_material_files()
            after_snapshot = workspace_snapshot()
            file_delta = build_file_delta(before_files, after_files)
            review_prompt = (
                f"Stage: review_after_codex_turn\n"
                f"Project kind: {project_kind}\n"
                f"Product name: {cfg.get('name')}\n"
                f"Goal: {cfg.get('goal')}\n"
                f"Turn: {turn}\n"
                f"Known acceptance checks: {json.dumps(acceptance_checks, ensure_ascii=False)}\n"
                f"Delivery bar: {json.dumps(acceptance_profile.get('delivery_bar', []), ensure_ascii=False)}\n"
                f"Stretch bar: {json.dumps(acceptance_profile.get('stretch_bar', []), ensure_ascii=False)}\n"
                f"Verification focus: {acceptance_profile.get('verification_focus', '')}\n\n"
                f"Workspace snapshot before turn:\n{before_snapshot}\n\n"
                f"Workspace snapshot after turn:\n{after_snapshot}\n\n"
                f"Material file delta:\n{file_delta}\n\n"
                f"Codex exit code: {rc}\n"
                f"Progress idle grace seconds: {progress_idle_grace}\n"
                f"Progress deadlock guard seconds: {progress_deadlock_guard}\n"
                f"Workspace progress signature after turn: {json.dumps(workspace_progress_signature(), ensure_ascii=False)}\n"
                f"Codex output excerpt:\n{last_codex_excerpt[-3000:]}\n\n"
                "Return JSON with exactly these fields: decision, summary, evidence, next_codex_task, delivery_summary, failure_reason.\n"
                "- decision must be one of: delegate, deliver, fail\n"
                "- evidence must be a short list of concrete observations from files/logs/output\n"
                "- next_codex_task must be the next specific implementation brief if decision=delegate\n"
                "- first judge whether the current evidence already satisfies the delivery bar for this project type\n"
                "- do not block delivery only because stretch-bar items are missing if the delivery bar is already met\n"
                "- for algorithm/research/theoretical work, a meaningful negative result, inconclusive result, benchmark finding, or falsified idea can still be a valid delivery if it is rigorous and useful\n"
                "- fail only if progress is blocked or evidence shows the current goal cannot be met reasonably"
            )
            review, review_raw = call_claw_json('review', review_prompt, timeout_seconds=120)
            decision = (review.get('decision') or '').strip().lower()
            summary = (review.get('summary') or '').strip()
            evidence = review.get('evidence') if isinstance(review.get('evidence'), list) else []
            if summary:
                append_user_claw_message(product_id, 'claw', f"Turn {turn} review: {summary}")
            if evidence:
                append_user_claw_message(product_id, 'claw', 'Evidence:\\n' + '\\n'.join(f'- {x}' for x in evidence[:8]))

            if decision == 'deliver':
                delivery_summary = (stringify_for_log(review.get('delivery_summary')) or summary or 'Claw judged the product delivered based on workspace evidence.').strip()
                log_claw(f'Claw marked product delivered on turn {turn}.')
                append_user_claw_message(product_id, 'claw', delivery_summary)
                set_state(status='delivered', lastError=None, stopRequested=False)
                return
            if decision == 'fail':
                failure_reason = (review.get('failure_reason') or summary or 'Claw marked the task failed after review.').strip()
                log_claw(f'Claw marked product failed on turn {turn}: {failure_reason}')
                append_user_claw_message(product_id, 'claw', failure_reason)
                set_state(status='failed', lastError=failure_reason, stopRequested=False)
                return

            next_task = (review.get('next_codex_task') or '').strip()
            if not next_task:
                next_task = default_codex_task(turn + 1, after_files)
                log_claw(f'Claw review did not provide next_codex_task on turn {turn}; using fallback task.')
            current_codex_task = next_task
            set_state(status='running', stopRequested=False, lastError=f'awaiting next iteration after turn {turn}')
            time.sleep(2)

        log_claw('Reached Claw supervision turn limit without delivery/final failure. Marking failed for now.')
        append_user_claw_message(product_id, 'claw', 'Claw supervision turn limit reached without delivery or final failure. Product marked failed for now.')
        set_state(status='failed', lastError=f'claw supervision turn limit reached (maxTurns={max_turns})', stopRequested=False)
    except Exception as e:
        log_claw(f'Run failed with exception: {e}')
        append_user_claw_message(product_id, 'claw', f'Run failed with exception: {e}')
        set_state(status='failed', lastError=str(e), stopRequested=False)
    finally:
        try:
            st_final = load_product_state(product_id)
            if st_final.get('status') == 'running':
                log_claw('Run is exiting while state is still running; applying reconcile fallback.')
                append_user_claw_message(product_id, 'claw', 'Run exited without a terminal state. Applying reconcile fallback based on the latest evidence.')
                if workspace_material_files():
                    set_state(status='failed', lastError='run exited without terminal decision; manual review recommended', stopRequested=False)
                else:
                    set_state(status='failed', lastError='run exited without producing deliverable evidence', stopRequested=False)
        except Exception as reconcile_error:
            log_claw(f'Reconcile fallback failed: {reconcile_error}')
        clear_active_run(product_id)

def language_switch_html(current_lang: str, base_path: str) -> str:
    return f"""
    <div class="flex items-center p-1 bg-slate-100 dark:bg-zinc-800 rounded-full border border-slate-200 dark:border-zinc-700">
      <a href="{html.escape(base_path)}?lang=en" class="px-3 py-1 rounded-full text-xs font-semibold {'bg-white dark:bg-zinc-700 shadow-sm text-slate-800 dark:text-slate-100' if current_lang == 'en' else 'text-slate-500 dark:text-zinc-400 hover:text-slate-800 dark:hover:text-slate-200 transition'}">EN</a>
      <a href="{html.escape(base_path)}?lang=zh" class="px-3 py-1 rounded-full text-xs font-semibold {'bg-white dark:bg-zinc-700 shadow-sm text-slate-800 dark:text-slate-100' if current_lang == 'zh' else 'text-slate-500 dark:text-zinc-400 hover:text-slate-800 dark:hover:text-slate-200 transition'}">中</a>
    </div>
    """


def page_template(title: str, body: str, lang: str, path: str = '/') -> bytes:
    html_lang = 'zh-CN' if lang == 'zh' else 'en'
    lang_switch = language_switch_html(lang, path)
    return f"""
<!doctype html>
<html lang="{html.escape(html_lang)}" class="light">
<head>
  <meta charset='utf-8'>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['Inter', 'system-ui', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          }},
          colors: {{
            brand: {{ 50: '#eff6ff', 100: '#dbeafe', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8', 900: '#1e3a8a', 950: '#172554' }},
            darkbg: '#09090b',
            darkcard: '#18181b',
          }}
        }}
      }}
    }}
  </script>
  <style type="text/tailwindcss">
    @layer components {{
      .badge {{ @apply inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold whitespace-nowrap border; }}
      .badge-running {{ @apply bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400 border-blue-200 dark:border-blue-500/30; }}
      .badge-delivered {{ @apply bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/30; }}
      .badge-failed {{ @apply bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400 border-red-200 dark:border-red-500/30; }}
      .badge-idle {{ @apply bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-400 border-slate-200 dark:border-zinc-700; }}
      .badge-stopped {{ @apply bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400 border-amber-200 dark:border-amber-500/30; }}
    }}
  </style>
  <style>
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 999px; }}
    .dark ::-webkit-scrollbar-thumb {{ background: #3f3f46; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
    .terminal-body::-webkit-scrollbar-thumb {{ background: #475569; }}
    body {{ -webkit-font-smoothing: antialiased; }}
    .chat-bubble-user {{ border-bottom-right-radius: 4px; }}
    .chat-bubble-bot {{ border-bottom-left-radius: 4px; }}
    .terminal-dot {{ width: 12px; height: 12px; border-radius: 999px; flex-shrink: 0; }}
    .dot-r {{ background: #ff5f56; box-shadow: 0 0 4px rgba(255,95,86,0.3); }}
    .dot-y {{ background: #ffbd2e; box-shadow: 0 0 4px rgba(255,189,46,0.3); }}
    .dot-g {{ background: #27c93f; box-shadow: 0 0 4px rgba(39,201,63,0.3); }}
    .copied {{ background: rgba(39,201,63,0.16) !important; border-color: rgba(39,201,63,0.28) !important; color: #d1fae5 !important; }}
  </style>
</head>
<body class="bg-slate-50 text-slate-900 dark:bg-darkbg dark:text-slate-100 transition-colors duration-200">
  <header class="sticky top-0 z-40 w-full backdrop-blur-md bg-white/80 dark:bg-darkcard/80 border-b border-slate-200 dark:border-zinc-800 transition-colors">
    <div class="max-w-[1460px] mx-auto px-6 h-16 flex items-center justify-between">
      <a href="/?lang={html.escape(lang)}" class="flex items-center gap-3 font-bold text-lg cursor-pointer hover:opacity-80 transition">
        <svg class="w-6 h-6 text-brand-600 dark:text-brand-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
        <span>TaskCaptain <span class="font-medium text-slate-500 dark:text-zinc-400">Workspace</span></span>
      </a>
      <div class="flex items-center gap-4">
        {lang_switch}
        <button onclick="toggleTheme()" class="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 text-slate-600 dark:text-zinc-400 transition" title="Toggle Light/Dark Theme">
          <svg id="icon-sun" class="w-5 h-5 hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
          <svg id="icon-moon" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-[1460px] mx-auto px-6 py-8">
    {body}
  </main>

  <script>
    function applyTheme(theme) {{
      const root = document.documentElement;
      const sun = document.getElementById('icon-sun');
      const moon = document.getElementById('icon-moon');
      if (theme === 'dark') {{
        root.classList.add('dark'); root.classList.remove('light');
        if(sun) sun.classList.remove('hidden');
        if(moon) moon.classList.add('hidden');
      }} else {{
        root.classList.add('light'); root.classList.remove('dark');
        if(sun) sun.classList.add('hidden');
        if(moon) moon.classList.remove('hidden');
      }}
      localStorage.setItem('taskcaptain-theme', theme);
    }}
    function toggleTheme() {{
      const isDark = document.documentElement.classList.contains('dark');
      applyTheme(isDark ? 'light' : 'dark');
    }}
    (function() {{
      const saved = localStorage.getItem('taskcaptain-theme') || 'light';
      applyTheme(saved);
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
        return f"<div class='flex-1 flex items-center justify-center p-8'><div class=\"text-center p-6 border border-dashed border-slate-300 dark:border-zinc-700 rounded-xl text-slate-500 dark:text-zinc-400 text-sm\">{html.escape(empty_text)}</div></div>"
    rows = []
    for x in items:
        role = x.get('role', '')
        is_user = role == 'user'
        if is_user:
            bubble_class = 'chat-bubble-user w-[85%] ml-auto bg-brand-50 border border-brand-100 dark:bg-brand-900/20 dark:border-brand-800/50 p-3.5 rounded-2xl shadow-sm'
            role_class = 'text-brand-600 dark:text-brand-400'
            role_display = 'USER'
        else:
            bubble_class = 'chat-bubble-bot w-[85%] bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 p-3.5 rounded-2xl shadow-sm'
            role_class = 'text-emerald-600 dark:text-emerald-400' if role == 'claw' else 'text-slate-500 dark:text-zinc-400'
            role_display = 'AGENT' if role == 'claw' else role.upper()
            if role == 'codex':
                bubble_class = 'chat-bubble-user w-[90%] ml-auto bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 p-3.5 rounded-2xl shadow-sm text-slate-700 dark:text-slate-300'

        header_content = ""
        if role == 'claw':
            header_content = f"<span class='text-xs font-bold {role_class} tracking-wider'>{html.escape(role_display)}</span><span class='text-[10px] font-mono text-slate-400'>{html.escape(x.get('ts', ''))}</span>"
        else:
            header_content = f"<span class='text-[10px] font-mono text-slate-400'>{html.escape(x.get('ts', ''))}</span><span class='text-xs font-bold {role_class} tracking-wider'>{html.escape(role_display)}</span>"

        rows.append(f"""
        <div class='{bubble_class} mb-4'>
          <div class='flex justify-between items-end mb-2'>
            {header_content}
          </div>
          <div class='text-sm font-mono leading-relaxed break-words whitespace-pre-wrap'>{html.escape(x.get('text', ''))}</div>
        </div>
        """)
    return ''.join(rows)


def badge_class_for(status: str) -> str:
    if status == 'running':
        return 'badge-running'
    if status in {'delivered', 'passed'}:
        return 'badge-delivered'
    if status == 'failed':
        return 'badge-failed'
    if status == 'stopped':
        return 'badge-stopped'
    return 'badge-idle'


def render_checks_html(checks: dict, lang: str) -> str:
    return ''.join(
        f"<tr class='border-b border-slate-100 dark:border-zinc-800 last:border-0'><td class='py-3 pr-4 font-semibold text-sm'>{html.escape(k)}</td><td class='py-3 px-4'><span class='inline-flex items-center px-2 py-0.5 rounded text-xs font-bold {'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400' if v.get('ok') else 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'}'>{'Pass' if v.get('ok') else 'Fail'}</span></td><td class='py-3 pl-4 font-mono text-xs text-slate-500 break-all'>{html.escape(str(v.get('detail', '')))}</td></tr>"
        for k, v in checks.items()
    ) or f"<tr><td colspan='3' class='py-4 text-slate-500 text-center text-sm'>{html.escape(t(lang, 'not_run'))}</td></tr>"


def build_product_live_payload(pid: str, lang: str) -> dict:
    d = product_dir(pid)
    cfg = load_product_config(pid)
    st = load_product_state(pid)
    self_test = st.get('selfTest', {})
    checks = self_test.get('checks', {})
    user_claw = st.get('conversations', {}).get('userClaw', [])[-30:]
    claw_codex = st.get('conversations', {}).get('clawCodex', [])[-30:]
    status = st.get('status', 'idle')
    st_status = self_test.get('status', 'not-run')
    is_running = status == 'running' and bool(active_run_info(pid))
    return {
        'status': status,
        'statusLabel': t(lang, status) if status in I18N[lang] else status,
        'statusClass': badge_class_for(status),
        'currentTurn': int(st.get('currentTurn') or 0),
        'maxTurns': int(cfg.get('maxTurns') or 8),
        'selfTestStatus': st_status,
        'selfTestStatusLabel': t(lang, st_status) if st_status in I18N[lang] else st_status,
        'selfTestStatusClass': badge_class_for(st_status),
        'selfTestRunning': st_status == 'running',
        'isRunning': is_running,
        'userClawHtml': render_dialogue(user_claw, t(lang, 'no_user_claw')),
        'clawCodexHtml': render_dialogue(claw_codex, t(lang, 'no_claw_codex')),
        'checksHtml': render_checks_html(checks, lang),
        'clawLog': (d / 'logs' / 'claw.log').read_text(encoding='utf-8') if (d / 'logs' / 'claw.log').exists() else t(lang, 'no_logs'),
        'codexLog': (d / 'logs' / 'codex.log').read_text(encoding='utf-8') if (d / 'logs' / 'codex.log').exists() else t(lang, 'no_logs'),
    }


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
        if parsed.path.startswith('/api/product-live/'):
            pid = parsed.path.split('/')[-1]
            return self.send_json(build_product_live_payload(pid, lang))
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
        if parsed.path.startswith('/set-max-turns/'):
            pid = parsed.path.split('/')[-1]
            cfg = load_product_config(pid)
            try:
                v = int((form.get('maxTurns') or '').strip() or str(cfg.get('maxTurns') or 8))
            except Exception:
                v = int(cfg.get('maxTurns') or 8)
            if v < 1:
                v = 1
            if v > 99:
                v = 99
            cfg['maxTurns'] = v
            save_product_config(pid, cfg)
            append_log(product_dir(pid) / 'logs' / 'claw.log', f"[{now_iso()}] Updated maxTurns to {v} via UI.")
            self.redirect(f'/product/{pid}?lang={lang}')
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
            result = start_self_test(pid)
            if result == 'already-running':
                append_user_claw_message(pid, 'claw', 'Self-test request ignored because a self-test is already running for this task.')
                append_log(product_dir(pid) / 'logs' / 'claw.log', f'[{now_iso()}] Ignored duplicate self-test request while a self-test was already running.')
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
            <label class='group flex gap-4 p-5 hover:bg-slate-50 dark:hover:bg-zinc-800/40 transition cursor-pointer' onclick="if(event.target.type!=='checkbox')window.location='/product/{pid}?lang={lang}'">
              <input class='mt-1 rounded border-slate-300 text-brand-600 focus:ring-brand-500 bg-white dark:bg-zinc-900 item-checkbox' type='checkbox' name='productIds' value='{html.escape(pid)}' {'disabled' if is_running else ''} onclick='event.stopPropagation()' />
              <div class='flex-1 min-w-0'>
                <div class='flex justify-between items-start gap-4 mb-1'>
                  <div>
                    <h3 class='text-lg font-semibold text-slate-900 dark:text-slate-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition'>{html.escape(cfg.get('name', t(lang, 'untitled')))}</h3>
                    <p class='text-xs text-slate-500 mt-0.5'>{html.escape(t(lang, 'profile_label'))}: {html.escape(claw_eff.get('profileName', '-'))}</p>
                  </div>
                  <span class='badge {badge_class_for(status)}'>
                    {html.escape(t(lang, status) if status in I18N[lang] else status)}
                  </span>
                </div>
                <p class='text-sm text-slate-600 dark:text-zinc-400 line-clamp-2 leading-relaxed mb-3'>{html.escape(goal_text)}</p>
                <div class='flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500 dark:text-zinc-500'>
                  <span>{html.escape(t(lang, 'created_at'))}: {html.escape(cfg.get('createdAt', ''))}</span>
                  <span>Agent: {html.escape(claw_eff.get('model', '-'))}</span>
                  <span>Codex: {html.escape(cfg.get('codex', {}).get('model', '-'))}</span>
                </div>
              </div>
            </label>
            """)

        profiles_html = ''.join(
            f"""
            <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl p-5 shadow-sm hover:shadow-md transition'>
              <div class='flex justify-between items-start gap-4 mb-3'>
                <h3 class='font-bold text-base'>{html.escape(p.get('name', ''))}</h3>
                <div class='text-right bg-slate-50 dark:bg-zinc-800/50 px-2 py-1.5 rounded-lg border border-slate-100 dark:border-zinc-700 text-xs'>
                  <span class='font-semibold block text-slate-700 dark:text-slate-300'>{html.escape(p.get('model', ''))}</span>
                  <span class='text-slate-400 dark:text-zinc-500'>Thinking: {html.escape(p.get('thinking', ''))}</span>
                </div>
              </div>
              <p class='text-sm text-slate-500 dark:text-zinc-400 line-clamp-2'>{html.escape(p.get('description', ''))}</p>
            </div>
            """
            for p in profiles
        ) or f'<div class="col-span-2 text-center py-8 text-slate-500 border border-dashed border-slate-300 dark:border-zinc-700 rounded-2xl">{html.escape(t(lang, "no_profiles"))}</div>'

        profile_options = ''.join(
            f"<option value='{html.escape(p.get('id', ''))}'>{html.escape(p.get('name', ''))}</option>" for p in profiles
        )

        input_cls = "w-full bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition"
        label_cls = "block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300"
        btn_primary_cls = "w-full bg-slate-900 hover:bg-black dark:bg-brand-600 dark:hover:bg-brand-500 text-white font-medium py-2.5 rounded-xl shadow-sm transition active:scale-[0.98]"
        btn_secondary_cls = "w-full px-4 py-2 font-semibold text-sm bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl shadow-sm hover:bg-slate-50 dark:hover:bg-zinc-700 transition active:scale-95"

        body = f"""
<div class='mb-8'>
  <h1 class='text-3xl font-bold tracking-tight mb-2'>{html.escape(t(lang, 'app_title'))}</h1>
  <p class='text-slate-500 dark:text-zinc-400'>{html.escape(t(lang, 'app_subtitle'))}</p>
</div>

<div class='grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-8 items-start'>
  <div class='space-y-10'>
    
    <section>
      <div class='flex items-center justify-between mb-4'>
        <h2 class='text-xl font-bold flex items-center gap-2'>{html.escape(t(lang, 'active_products'))}</h2>
      </div>
      
      <form method='post' action='/bulk-delete' onsubmit='return confirm({json.dumps(t(lang, 'bulk_delete_confirm'))});'>
        <input type='hidden' name='lang' value='{html.escape(lang)}' />
        <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden'>
          <div class='bg-slate-50/50 dark:bg-zinc-800/20 px-4 py-3 border-b border-slate-200 dark:border-zinc-800 flex justify-between items-center'>
            <label class='flex items-center gap-2 text-sm font-medium cursor-pointer'>
              <input type='checkbox' class='rounded border-slate-300 text-brand-600 focus:ring-brand-500 bg-white dark:bg-zinc-900' onchange='toggleAllCheckboxes(this)'>
              <span>{html.escape(t(lang, 'select_for_bulk_delete'))}</span>
            </label>
            <div class='flex items-center gap-3'>
              <span class='text-xs text-slate-400'>{html.escape(t(lang, 'running_skip_note'))}</span>
              <button type='submit' class='text-xs font-semibold px-3 py-1.5 bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-500/10 dark:text-red-400 dark:hover:bg-red-500/20 rounded-lg transition'>{html.escape(t(lang, 'bulk_delete'))}</button>
            </div>
          </div>
          <div class='divide-y divide-slate-100 dark:divide-zinc-800'>
            {''.join(product_rows) if product_rows else f"<div class='p-8 text-center text-slate-500'>{html.escape(t(lang, 'no_products'))}</div>"}
          </div>
        </div>
      </form>
    </section>

    <section>
      <div class='flex items-center justify-between mb-4'>
        <h2 class='text-xl font-bold'>{html.escape(t(lang, 'reusable_claw_profiles'))}</h2>
      </div>
      <p class='text-sm text-slate-500 dark:text-zinc-400 mb-4 max-w-3xl leading-relaxed'>{html.escape(t(lang, 'claw_identity_body'))}</p>
      <div class='grid grid-cols-1 md:grid-cols-2 gap-4'>
        {profiles_html}
      </div>
    </section>

  </div>

  <div class='xl:sticky xl:top-24 space-y-6'>
    
    <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden flex flex-col'>
      <div class='bg-slate-50/80 dark:bg-zinc-800/40 px-5 py-4 border-b border-slate-200 dark:border-zinc-800'>
        <h3 class='font-bold text-[0.95rem] flex items-center gap-2 tracking-wide uppercase'>
          <span class='text-brand-500'>✦</span> {html.escape(t(lang, 'create_product'))}
        </h3>
      </div>
      <div class='p-5 flex-1'>
        <form method='post' action='/create' class='space-y-4'>
          <input type='hidden' name='lang' value='{html.escape(lang)}' />
          <div>
            <label class='{label_cls} text-sm'>{html.escape(t(lang, 'product_name'))}</label>
            <input name='name' placeholder='e.g. My Awesome App' class='{input_cls} py-2.5' />
          </div>
          <div>
            <label class='{label_cls} text-sm'>{html.escape(t(lang, 'goal'))}</label>
            <textarea name='goal' rows='2' placeholder='{html.escape(t(lang, 'goal_placeholder'))}' class='{input_cls} py-2.5 resize-y'></textarea>
          </div>
          <div>
            <label class='{label_cls} text-sm'>{html.escape(t(lang, 'max_turns'))}</label>
            <input type='number' name='maxTurns' min='1' max='99' value='8' class='{input_cls}' />
            <p class='text-xs text-slate-500 dark:text-zinc-400 mt-1 leading-relaxed'>{html.escape(t(lang, 'max_turns_help'))}</p>
          </div>
          <div>
            <label class='{label_cls} text-sm'>{html.escape(t(lang, 'product_folder'))}</label>
            <input name='productFolder' value='' placeholder='{html.escape(DEFAULT_PRODUCT_FOLDER)}' class='{input_cls}' />
          </div>
          
          <div class='bg-slate-50/50 dark:bg-zinc-800/30 border border-slate-200 dark:border-zinc-800 rounded-xl p-4 space-y-3'>
            <h4 class='text-xs font-bold text-slate-400 uppercase tracking-wider'>{html.escape(t(lang, 'claw_setting'))}</h4>
            <div>
              <label class='{label_cls}'>{html.escape(t(lang, 'claw_profile_select'))}</label>
              <select name='clawProfileId' class='w-full bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500'>{profile_options}</select>
            </div>
            <details class='group'>
              <summary class='text-xs font-medium text-brand-600 dark:text-brand-400 cursor-pointer hover:underline outline-none select-none'>+ 展开高级配置 (API, Model, Soul...)</summary>
              <div class='pt-3 space-y-3'>
                <div class='grid grid-cols-2 gap-3'>
                  <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_endpoint'))}</label><input name='clawEndpoint' value='{html.escape(DEFAULT_AGENT_ENDPOINT)}' class='{input_cls}' /></div>
                  <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_api_key'))}</label><input type='password' name='clawApiKey' class='{input_cls}' /></div>
                </div>
                <div class='grid grid-cols-2 gap-3'>
                  <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_model'))}</label><input name='clawModel' placeholder='{html.escape(default_profile.get('model', ''))}' class='{input_cls}' /></div>
                  <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_thinking'))}</label><input name='clawThinking' placeholder='{html.escape(default_profile.get('thinking', ''))}' class='{input_cls}' /></div>
                </div>
                <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_soul'))}</label><textarea name='clawSoul' rows='2' placeholder='{html.escape(t(lang, 'profile_soul_placeholder'))}' class='{input_cls}'></textarea></div>
                <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_skills'))}</label><textarea name='clawSkills' rows='2' placeholder='{html.escape(t(lang, 'profile_skills_placeholder'))}' class='{input_cls}'></textarea></div>
              </div>
            </details>
          </div>

          <div class='bg-slate-50/50 dark:bg-zinc-800/30 border border-slate-200 dark:border-zinc-800 rounded-xl p-4 space-y-3'>
            <h4 class='text-xs font-bold text-slate-400 uppercase tracking-wider'>{html.escape(t(lang, 'codex_setting'))}</h4>
            <div class='grid grid-cols-2 gap-3'>
              <div><label class='{label_cls}'>{html.escape(t(lang, 'codex_endpoint'))}</label><input name='codexEndpoint' value='{html.escape(DEFAULT_CODEX_ENDPOINT)}' class='{input_cls}' /></div>
              <div><label class='{label_cls}'>{html.escape(t(lang, 'codex_api_key'))}</label><input type='password' name='codexApiKey' class='{input_cls}' /></div>
            </div>
            <div class='grid grid-cols-2 gap-3'>
              <div><label class='{label_cls}'>{html.escape(t(lang, 'codex_model'))}</label><input name='codexModel' value='gpt-5.4-medium' class='{input_cls}' /></div>
              <div><label class='{label_cls}'>{html.escape(t(lang, 'codex_thinking'))}</label><input name='codexThinking' value='medium' class='{input_cls}' /></div>
            </div>
            <div class='flex gap-4 mt-2'>
              <label class='flex items-center gap-2 text-sm font-medium cursor-pointer'>
                <input type='checkbox' name='codexPlanMode' checked class='rounded border-slate-300 text-brand-600 focus:ring-brand-500 bg-white dark:bg-zinc-900'>
                <span>{html.escape(t(lang, 'enable_plan'))}</span>
              </label>
              <label class='flex items-center gap-2 text-sm font-medium cursor-pointer'>
                <input type='checkbox' name='codexMaxPermission' checked class='rounded border-slate-300 text-brand-600 focus:ring-brand-500 bg-white dark:bg-zinc-900'>
                <span>{html.escape(t(lang, 'enable_max_permission'))}</span>
              </label>
            </div>
          </div>

          <button type='submit' class='{btn_primary_cls}'>{html.escape(t(lang, 'create_button'))}</button>
        </form>
      </div>
    </div>

    <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden flex flex-col'>
      <div class='bg-slate-50/80 dark:bg-zinc-800/40 px-5 py-4 border-b border-slate-200 dark:border-zinc-800'>
        <h3 class='font-bold text-[0.95rem] flex items-center gap-2 tracking-wide uppercase'>
          <span class='text-slate-400'>+</span> {html.escape(t(lang, 'create_profile'))}
        </h3>
      </div>
      <div class='p-5 flex-1'>
        <form method='post' action='/profiles/create' class='space-y-4'>
          <input type='hidden' name='lang' value='{html.escape(lang)}' />
          <div><label class='{label_cls}'>{html.escape(t(lang, 'profile_name'))}</label><input name='profileName' placeholder='e.g. Sandrone Network Auditor' class='{input_cls}' /></div>
          <div><label class='{label_cls}'>{html.escape(t(lang, 'profile_description'))}</label><input name='profileDescription' placeholder='{html.escape(t(lang, 'profile_desc_placeholder'))}' class='{input_cls}' /></div>
          <div class='grid grid-cols-2 gap-3'>
            <div><label class='{label_cls}'>{html.escape(t(lang, 'profile_model_hint'))}</label><input name='profileModel' value='{html.escape(default_profile.get('model', ''))}' class='{input_cls}' /></div>
            <div><label class='{label_cls}'>{html.escape(t(lang, 'profile_thinking_hint'))}</label><input name='profileThinking' value='{html.escape(default_profile.get('thinking', ''))}' class='{input_cls}' /></div>
          </div>
          <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_soul'))}</label><textarea name='profileSoul' rows='2' class='{input_cls}'>{html.escape(default_profile.get('soul', ''))}</textarea></div>
          <div><label class='{label_cls}'>{html.escape(t(lang, 'claw_skills'))}</label><textarea name='profileSkills' rows='2' class='{input_cls}'>{html.escape(default_profile.get('skills', ''))}</textarea></div>
          <button type='submit' class='{btn_secondary_cls} mt-2'>{html.escape(t(lang, 'create_profile_button'))}</button>
        </form>
      </div>
    </div>

  </div>
</div>
"""
        self.send_html(page_template(t(lang, 'app_title'), body, lang, '/'))

    def render_product(self, pid: str, lang: str):
        cfg = load_product_config(pid)
        st = load_product_state(pid)
        claw_eff = effective_claw_config(cfg)
        live = build_product_live_payload(pid, lang)
        profile = load_claw_profile(claw_eff.get('profileId'))

        input_cls = "w-full bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition"
        label_cls = "block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300"
        btn_secondary_cls = "px-4 py-2 font-semibold text-sm bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl shadow-sm hover:bg-slate-50 dark:hover:bg-zinc-700 transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"

        body = f"""
<a href='/?lang={lang}' class='inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-slate-100 mb-6 transition'>
  <svg class='w-4 h-4' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path stroke-linecap='round' stroke-linejoin='round' d='M10 19l-7-7m0 0l7-7m-7 7h18' /></svg>
  {html.escape(t(lang, 'back'))}
</a>

<div class='flex flex-wrap items-start justify-between gap-6 mb-8'>
  <div>
    <h1 class='text-3xl font-bold flex items-center flex-wrap gap-3 mb-2'>
      {html.escape(cfg.get('name', t(lang, 'untitled')))}
      <span class='badge {live['statusClass']}' id='product-status-badge'>{html.escape(live['statusLabel'])}</span>
      <span class='badge {live['selfTestStatusClass']}' id='self-test-status-badge' data-label-prefix='{html.escape(t(lang, 'self_test'))}: '>{html.escape(t(lang, 'self_test'))}: {html.escape(live['selfTestStatusLabel'])}</span>
      <span class='badge badge-idle' id='turn-progress-badge' data-label-prefix='{html.escape(t(lang, 'turn_progress'))}: '>{html.escape(t(lang, 'turn_progress'))}: {int(st.get('currentTurn') or 0)}/{int(cfg.get('maxTurns') or 8)}</span>
    </h1>
    <div class='font-mono text-sm text-slate-500 dark:text-zinc-400 flex gap-4 flex-wrap'>
      <span>ID: {html.escape(pid)}</span>
      <span>Dir: {html.escape(cfg.get('productFolder', ''))}</span>
    </div>
  </div>
  
  <div class='flex flex-wrap items-center gap-3'>
    <form method='post' action='/selftest/{html.escape(pid)}' class='m-0'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='{btn_secondary_cls}' id='run-self-test-btn' {'disabled' if live['selfTestRunning'] else ''}>{html.escape(t(lang, 'run_self_test'))}</button>
    </form>
    <form method='post' action='/start/{html.escape(pid)}' class='m-0'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='px-4 py-2 font-semibold text-sm bg-slate-900 hover:bg-black dark:bg-brand-600 dark:hover:bg-brand-500 text-white rounded-xl shadow-sm transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed' id='start-run-btn' {'disabled' if live['isRunning'] else ''}>{html.escape(t(lang, 'start_continue_run'))}</button>
    </form>
    <form method='post' action='/stop/{html.escape(pid)}' class='m-0'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='{btn_secondary_cls}' id='stop-run-btn' {'disabled' if not live['isRunning'] else ''}>{html.escape(t(lang, 'stop_run'))}</button>
    </form>
    <form method='post' action='/delete/{html.escape(pid)}' class='m-0' onsubmit='return confirm({json.dumps(t(lang, 'delete_confirm'))});'>
      <input type='hidden' name='lang' value='{html.escape(lang)}' />
      <button type='submit' class='p-2 bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-500/10 dark:text-red-400 dark:hover:bg-red-500/20 rounded-xl transition active:scale-95 ml-2 disabled:opacity-50 disabled:cursor-not-allowed' id='delete-product-btn' {'disabled' if live['isRunning'] else ''} title='{html.escape(t(lang, 'delete_product'))}'>
        <svg class='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path stroke-linecap='round' stroke-linejoin='round' d='M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' /></svg>
      </button>
    </form>
  </div>
</div>

<div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm mb-6 overflow-hidden'>
  <div class='bg-slate-50/80 dark:bg-zinc-800/40 px-5 py-4 border-b border-slate-200 dark:border-zinc-800'>
    <h3 class='font-bold uppercase tracking-wider text-sm'>{html.escape(t(lang, 'configuration_details'))}</h3>
  </div>
  <div class='grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100 dark:divide-zinc-800 p-5 gap-6 md:gap-0'>
    <div class='md:pr-6'>
      <h4 class='text-xs font-bold text-slate-400 uppercase tracking-wider mb-2'>{html.escape(t(lang, 'goal'))}</h4>
      <div class='text-sm bg-slate-50 dark:bg-zinc-800/50 p-3 rounded-xl border border-slate-100 dark:border-zinc-800 leading-relaxed whitespace-pre-wrap'>{html.escape(cfg.get('goal', ''))}</div>
    </div>
    <div class='md:px-6'>
      <h4 class='text-xs font-bold text-slate-400 uppercase tracking-wider mb-2'>{html.escape(t(lang, 'claw_setting'))}</h4>
      <ul class='text-sm space-y-2'>
        <li><b class='text-slate-700 dark:text-slate-300'>{html.escape(t(lang, 'profile_label'))}:</b> {html.escape(claw_eff.get('profileName', ''))}</li>
        <li><b class='text-slate-700 dark:text-slate-300'>{html.escape(t(lang, 'model'))}:</b> {html.escape(claw_eff.get('model', ''))} <span class='text-slate-400'>({html.escape(claw_eff.get('thinking', ''))})</span></li>
        <li><b class='text-slate-700 dark:text-slate-300'>{html.escape(t(lang, 'api_key_present'))}:</b> <span class='{'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30' if claw_eff.get('apiKey') else 'text-red-600 bg-red-50 dark:bg-red-900/30'} px-1.5 rounded text-xs'>{html.escape(t(lang, mask_present(claw_eff.get('apiKey'))))}</span></li>
        <li class='font-mono text-xs text-slate-500 mt-1 break-all'>{html.escape(claw_eff.get('endpoint', ''))}</li>
      </ul>
    </div>
    <div class='md:pl-6'>
      <h4 class='text-xs font-bold text-slate-400 uppercase tracking-wider mb-2'>{html.escape(t(lang, 'codex_setting'))}</h4>
      <ul class='text-sm space-y-2'>
        <li><b class='text-slate-700 dark:text-slate-300'>{html.escape(t(lang, 'model'))}:</b> {html.escape(cfg.get('codex', {}).get('model', ''))} <span class='text-slate-400'>({html.escape(cfg.get('codex', {}).get('thinking', ''))})</span></li>
        <li><b class='text-slate-700 dark:text-slate-300'>{html.escape(t(lang, 'api_key_present'))}:</b> <span class='{'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30' if cfg.get('codex', {}).get('apiKey') else 'text-red-600 bg-red-50 dark:bg-red-900/30'} px-1.5 rounded text-xs'>{html.escape(t(lang, mask_present(cfg.get('codex', {}).get('apiKey'))))}</span></li>
        <li class='font-mono text-xs text-slate-500 mt-1 break-all'>{html.escape(cfg.get('codex', {}).get('endpoint', ''))}</li>
        <li>
          <b class='text-slate-700 dark:text-slate-300'>{html.escape(t(lang, 'max_turns'))}:</b>
          <form method='post' action='/set-max-turns/{html.escape(pid)}' class='inline-flex items-center gap-2 ml-2 align-middle'>
            <input type='hidden' name='lang' value='{html.escape(lang)}' />
            <input type='number' name='maxTurns' min='1' max='99' value='{html.escape(str(int(cfg.get('maxTurns') or 8)))}' class='w-20 bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition' />
            <button type='submit' class='px-2.5 py-1 text-xs font-semibold bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg hover:bg-slate-50 dark:hover:bg-zinc-700 transition'>保存</button>
          </form>
        </li>

        <li class='flex gap-2 mt-2'>
          <span class='text-[10px] uppercase font-bold bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 rounded border border-slate-200 dark:border-zinc-700'>Plan: {cfg.get('codex', {}).get('planMode')}</span>
          <span class='text-[10px] uppercase font-bold bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 rounded border border-slate-200 dark:border-zinc-700'>MaxPerm: {cfg.get('codex', {}).get('maxPermission')}</span>
        </li>
      </ul>
    </div>
  </div>
</div>

<div class='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6'>
  
  <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm flex flex-col h-[500px]'>
    <div class='bg-slate-50/80 dark:bg-zinc-800/40 px-5 py-4 border-b border-slate-200 dark:border-zinc-800 shrink-0'>
      <h3 class='font-bold uppercase tracking-wider text-sm flex items-center justify-between'>
        {html.escape(t(lang, 'user_claw_dialogue'))}
        <span class='w-2 h-2 rounded-full bg-brand-500 animate-pulse {'hidden' if not live['isRunning'] else ''}'></span>
      </h3>
    </div>
    <div id='user-claw-dialogue' class='flex-1 overflow-y-auto bg-slate-50/30 dark:bg-zinc-900/30'>{live['userClawHtml']}</div>
    <div class='p-4 border-t border-slate-200 dark:border-zinc-800 bg-white dark:bg-darkcard rounded-b-2xl shrink-0'>
      <form method='post' action='/append-user/{html.escape(pid)}' class='flex gap-3 m-0'>
        <input type='hidden' name='lang' value='{html.escape(lang)}' />
        <input type='text' name='message' placeholder='{html.escape(t(lang, 'append_placeholder'))}' required class='flex-1 bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition'>
        <button type='submit' class='px-5 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl shadow-sm transition active:scale-95 whitespace-nowrap'>{html.escape(t(lang, 'append_button'))}</button>
      </form>
    </div>
  </div>

  <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm flex flex-col h-[500px]'>
    <div class='bg-slate-50/80 dark:bg-zinc-800/40 px-5 py-4 border-b border-slate-200 dark:border-zinc-800 shrink-0'>
      <h3 class='font-bold uppercase tracking-wider text-sm'>{html.escape(t(lang, 'claw_codex_dialogue'))}</h3>
    </div>
    <div id='claw-codex-dialogue' class='flex-1 overflow-y-auto bg-slate-50/30 dark:bg-zinc-900/30 rounded-b-2xl'>{live['clawCodexHtml']}</div>
  </div>

</div>

<div class='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8'>
  
  <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm flex flex-col'>
    <div class='bg-slate-50/80 dark:bg-zinc-800/40 px-5 py-4 border-b border-slate-200 dark:border-zinc-800'>
      <h3 class='font-bold uppercase tracking-wider text-sm'>{html.escape(t(lang, 'save_current_claw_profile'))}</h3>
    </div>
    <div class='p-5'>
      <p class='text-sm text-slate-500 dark:text-zinc-400 mb-4'>{html.escape(t(lang, 'profile_saved_hint'))}</p>
      <form method='post' action='/save-profile/{html.escape(pid)}' class='space-y-4 m-0'>
        <input type='hidden' name='lang' value='{html.escape(lang)}' />
        <div><label class='{label_cls}'>{html.escape(t(lang, 'profile_name'))}</label><input name='profileName' placeholder='{html.escape(claw_eff.get('profileName', ''))}' class='{input_cls}' /></div>
        <div><label class='{label_cls}'>{html.escape(t(lang, 'profile_description'))}</label><input name='profileDescription' placeholder='{html.escape(t(lang, 'profile_desc_placeholder'))}' class='{input_cls}' /></div>
        <button type='submit' class='{btn_secondary_cls} w-full mt-2'>{html.escape(t(lang, 'save_profile_button'))}</button>
      </form>
    </div>
  </div>

  <div class='bg-white dark:bg-darkcard border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm flex flex-col'>
    <div class='bg-slate-50/80 dark:bg-zinc-800/40 px-5 py-4 border-b border-slate-200 dark:border-zinc-800 flex justify-between items-center'>
      <h3 class='font-bold uppercase tracking-wider text-sm'>{html.escape(t(lang, 'self_test_details'))}</h3>
      <span class='badge {live['selfTestStatusClass']}' id='self-test-details-badge'>{html.escape(live['selfTestStatusLabel'])}</span>
    </div>
    <div class='flex-1 overflow-y-auto max-h-[300px]'>
      <table class='w-full text-left border-collapse'>
        <thead class='bg-slate-50 dark:bg-zinc-900/50 text-xs uppercase text-slate-400 border-b border-slate-200 dark:border-zinc-800 sticky top-0'>
          <tr>
            <th class='py-3 pl-5 pr-4 font-semibold w-1/4'>{html.escape(t(lang, 'check'))}</th>
            <th class='py-3 px-4 font-semibold w-24'>{html.escape(t(lang, 'result'))}</th>
            <th class='py-3 px-5 font-semibold'>{html.escape(t(lang, 'detail'))}</th>
          </tr>
        </thead>
        <tbody id='self-test-checks-body' class='divide-y divide-slate-100 dark:divide-zinc-800 px-5 text-sm'>
          {live['checksHtml']}
        </tbody>
      </table>
    </div>
    <div class='p-4 border-t border-slate-200 dark:border-zinc-800 bg-slate-50/30 dark:bg-zinc-900/30 rounded-b-2xl'>
      <form method='post' action='/selftest/{html.escape(pid)}' class='m-0'>
        <input type='hidden' name='lang' value='{html.escape(lang)}' />
        <button type='submit' class='{btn_secondary_cls} w-full' id='run-self-test-btn-bottom' {'disabled' if live['selfTestRunning'] else ''}>{html.escape(t(lang, 'run_self_test'))}</button>
      </form>
    </div>
  </div>

</div>

<div class='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8'>
  
  <div class='bg-[#0f172a] dark:bg-[#000000] border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col h-[360px]'>
    <div class='flex justify-between items-center px-4 py-2.5 bg-white/5 border-b border-white/10 shrink-0'>
      <div class='flex items-center gap-2'>
        <div class='flex gap-1.5 mr-3'>
          <div class='terminal-dot dot-r'></div><div class='terminal-dot dot-y'></div><div class='terminal-dot dot-g'></div>
        </div>
        <span class='text-xs font-mono text-slate-400'>~/{html.escape(t(lang, 'claw_log'))}</span>
      </div>
      <button type='button' class='text-[11px] font-mono text-slate-300 bg-white/10 hover:bg-white/20 border border-white/10 rounded-full px-2.5 py-1 transition copy-btn' data-copy-target='claw-log-body'>复制全部</button>
    </div>
    <div class='flex-1 p-4 overflow-y-auto font-mono text-[13px] text-slate-300 leading-relaxed terminal-body whitespace-pre-wrap break-all' id='claw-log-body'>{html.escape(live['clawLog'])}</div>
  </div>

  <div class='bg-[#0f172a] dark:bg-[#000000] border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col h-[360px]'>
    <div class='flex justify-between items-center px-4 py-2.5 bg-white/5 border-b border-white/10 shrink-0'>
      <div class='flex items-center gap-2'>
        <div class='flex gap-1.5 mr-3'>
          <div class='terminal-dot dot-r'></div><div class='terminal-dot dot-y'></div><div class='terminal-dot dot-g'></div>
        </div>
        <span class='text-xs font-mono text-slate-400'>~/{html.escape(t(lang, 'codex_log'))}</span>
      </div>
      <button type='button' class='text-[11px] font-mono text-slate-300 bg-white/10 hover:bg-white/20 border border-white/10 rounded-full px-2.5 py-1 transition copy-btn' data-copy-target='codex-log-body'>复制全部</button>
    </div>
    <div class='flex-1 p-4 overflow-y-auto font-mono text-[13px] text-slate-300 leading-relaxed terminal-body whitespace-pre-wrap break-all' id='codex-log-body'>{html.escape(live['codexLog'])}</div>
  </div>

</div>

<script>
(function() {{
  function preserveScroll(el, updater) {{
    if (!el) return;
    const fromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    updater();
    el.scrollTop = Math.max(0, el.scrollHeight - el.clientHeight - fromBottom);
  }}

  function wireCopyButtons() {{
    document.querySelectorAll('[data-copy-target]').forEach(btn => {{
      if (btn.dataset.copyBound === '1') return;
      btn.dataset.copyBound = '1';
      btn.addEventListener('click', async () => {{
        const el = document.getElementById(btn.getAttribute('data-copy-target'));
        if (!el) return;
        const original = btn.textContent;
        try {{
          await navigator.clipboard.writeText(el.innerText || el.textContent || '');
          btn.textContent = '已复制';
          btn.classList.add('copied');
        }} catch (e) {{
          btn.textContent = '失败';
        }}
        setTimeout(() => {{
          btn.textContent = original;
          btn.classList.remove('copied');
        }}, 1200);
      }});
    }});
  }}

  async function refreshProductLive() {{
    try {{
      const resp = await fetch('/api/product-live/{html.escape(pid)}?lang={html.escape(lang)}', {{ cache: 'no-store' }});
      if (!resp.ok) return;
      const data = await resp.json();

      const statusBadge = document.getElementById('product-status-badge');
      if (statusBadge) {{
        statusBadge.className = 'badge ' + data.statusClass;
        statusBadge.textContent = data.statusLabel;
      }}


      const turnProgressBadge = document.getElementById('turn-progress-badge');
      if (turnProgressBadge) {{
        const prefix = turnProgressBadge.dataset.labelPrefix || '';
        const currentTurn = (data.currentTurn || 0);
        const maxTurns = (data.maxTurns || 0);
        turnProgressBadge.textContent = prefix + currentTurn + '/' + (maxTurns || '-');
        turnProgressBadge.className = 'badge ' + (data.isRunning ? 'badge-running' : 'badge-idle');
      }}

      const selfTestBadge = document.getElementById('self-test-status-badge');
      if (selfTestBadge) {{
        selfTestBadge.className = 'badge ' + data.selfTestStatusClass;
        selfTestBadge.textContent = (selfTestBadge.dataset.labelPrefix || '') + data.selfTestStatusLabel;
      }}

      const selfTestDetailsBadge = document.getElementById('self-test-details-badge');
      if (selfTestDetailsBadge) {{
        selfTestDetailsBadge.className = 'badge ' + data.selfTestStatusClass;
        selfTestDetailsBadge.textContent = data.selfTestStatusLabel;
      }}

      const runSelfTestBtn = document.getElementById('run-self-test-btn');
      if (runSelfTestBtn) runSelfTestBtn.disabled = !!data.selfTestRunning;
      const runSelfTestBtnBottom = document.getElementById('run-self-test-btn-bottom');
      if (runSelfTestBtnBottom) runSelfTestBtnBottom.disabled = !!data.selfTestRunning;
      const startRunBtn = document.getElementById('start-run-btn');
      if (startRunBtn) startRunBtn.disabled = !!data.isRunning;
      const stopRunBtn = document.getElementById('stop-run-btn');
      if (stopRunBtn) stopRunBtn.disabled = !data.isRunning;
      const deleteBtn = document.getElementById('delete-product-btn');
      if (deleteBtn) deleteBtn.disabled = !!data.isRunning;

      const userClaw = document.getElementById('user-claw-dialogue');
      preserveScroll(userClaw, () => {{ if (userClaw) userClaw.innerHTML = data.userClawHtml; }});
      const clawCodex = document.getElementById('claw-codex-dialogue');
      preserveScroll(clawCodex, () => {{ if (clawCodex) clawCodex.innerHTML = data.clawCodexHtml; }});
      const checksBody = document.getElementById('self-test-checks-body');
      if (checksBody) checksBody.innerHTML = data.checksHtml;
      const clawLog = document.getElementById('claw-log-body');
      preserveScroll(clawLog, () => {{ if (clawLog) clawLog.textContent = data.clawLog; }});
      const codexLog = document.getElementById('codex-log-body');
      preserveScroll(codexLog, () => {{ if (codexLog) codexLog.textContent = data.codexLog; }});
    }} catch (e) {{}}
  }}

  wireCopyButtons();
  setInterval(refreshProductLive, 5000);
}})();
</script>
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