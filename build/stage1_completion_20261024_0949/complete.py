"""Finish the single already-running G3 build; never launch CAD or simulation.

Stop this Python process as well as the route wrapper if Jeremy pauses work.
No Git push, board access, Flash write or replacement of old deliveries.
"""
from pathlib import Path
import contextlib, datetime, json, os, subprocess, sys, time, traceback, zipfile

O = Path(__file__).resolve().parent
R = O.parents[1]
sys.path.insert(0, str(R / 'scripts'))
from audit_stage1 import audit, sha
from stage1_policy import canonical_build_inputs

ATTEMPT = 'build/stage1_route_20261024_092334_800316'
route = R / ATTEMPT
compiler = '555020828e32058ec6b7a3c7f61045b4c5cbbcab'
watched = [R / n for n in ('README.md', 'reports/stage1/validation.md',
           'docs/区域顺序_第一阶段_执行记录.md', 'scripts/package_stage1.py',
           'scripts/audit_stage1.py', 'scripts/verify_stage1_delivery.py',
           'scripts/run_stage1_route.py')]
before = {p: p.read_bytes() for p in watched}
expected = {p: sha(p) for p in watched}
self_hash = sha(Path(__file__))

def save(name, obj):
    with (O / name).open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

try:
    context = json.loads((route / 'source_context.json').read_text())
    assert context['compiled_source_commit'] == compiler
    inputs = json.loads((route / 'inputs.json').read_text())
    canonical_build_inputs(inputs)
    proof = audit()
    assert proof['passed'] == proof['required'] == 112 and not proof['missing']
    save('started.json', dict(status='WAITING_FOR_EXISTING_ROUTE_ONLY', pid=os.getpid(),
         started=datetime.datetime.now().isoformat(), attempt=ATTEMPT,
         compiled_source_commit=compiler, software_checks=112,
         watched_files={p.relative_to(R).as_posix(): h for p, h in expected.items()},
         producer_sha256=self_hash))
    print('G3_COMPLETION_WAITING', os.getpid(), ATTEMPT, flush=True)
    while not (route / 'summary.json').is_file():
        time.sleep(5)
        assert sha(Path(__file__)) == self_hash, 'Completion producer changed'
    # The existing wrapper writes summary only after CAD has exited. Native
    # failure, residual conflicts, bad timing or stale software are rejected.
    assert all(sha(p) == h for p, h in expected.items()), 'User/current files changed; preserve them'
    canonical_build_inputs(inputs)
    proof = audit(ATTEMPT)
    assert proof['passed'] == proof['required'] == 112
    assert proof['build']['compiled_source_commit'] == compiler
    assert proof['build']['routing']['routing_drc_pass']
    summary = proof['build']['summary']
    save('physical_audit.json', proof)
    with zipfile.ZipFile(O / 'before_delivery_docs.zip', 'x', zipfile.ZIP_DEFLATED) as z:
        for p, data in before.items():
            z.writestr(p.relative_to(R).as_posix(), data)
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    measured = json.dumps(summary['resources'], ensure_ascii=False)
    slack = json.dumps(summary['slack_ns'], ensure_ascii=False)
    description = (f'当前G3源码112/112项软件检查及本次最终零冲突Routing DRC已通过，'
                   f'最终资源{measured}；建立/保持余量(ns){slack}，均非负。'
                   '以下调用严格同源打包与独立校验；只有build交付目录中具有通过状态的'
                   'delivery.json、SHA256SUMS.txt、bit和同源ZIP时，才可作为待上板候选。'
                   '实物验收仍待执行，未推送、未上板、未烧Flash。')
    p = R / 'README.md'
    needle = 'G3最终布线进行中，零冲突DRC和非负建立/保持尚待完成，无本阶段可交付bit。'.encode()
    assert before[p].count(needle) == 1
    p.write_bytes(before[p].replace(needle, description.encode()))
    section = ('## ' + stamp + '：G3最终物理审计通过，待同源包校验\r\n\r\n'
               + description + '\r\n\r\n构建来源：`' + ATTEMPT
               + '`；编译提交`' + compiler + '`。全部308源码/冻结输入/原始Git字节、'
               '置入检查点、原约束及当前软件证据已核验。旧交付与用户文件保留。\r\n\r\n').encode()
    p = R / 'reports/stage1/validation.md'; p.write_bytes(section + before[p])
    p = R / 'docs/区域顺序_第一阶段_执行记录.md'; p.write_bytes(before[p] + b'\r\n' + section)
    with (O / 'packaging.log').open('x', encoding='utf8') as log, contextlib.redirect_stdout(log):
        from package_stage1 import package
        destination = package(ATTEMPT)
        independent = subprocess.run([sys.executable, '-X', 'utf8',
            str(R / 'scripts/verify_stage1_delivery.py'), str(destination)],
            cwd=R, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        assert independent.returncode == 0, 'Separate delivery verification failed'
    delivery = json.loads((destination / 'delivery.json').read_text(encoding='utf8'))
    assert delivery['stage1_checks'] == 112
    save('outcome.json', dict(status='VERIFIED_CANDIDATE_AWAITING_USER_DELIVERY_AND_BOARD_TEST',
         completed=datetime.datetime.now().isoformat(), directory=str(destination),
         delivery=delivery, no_push_board_or_flash=True))
    agents = R.parent / 'AGENTS.md'
    old = agents.read_bytes()
    insert = ('## ' + stamp + '：G3候选同源包与独立校验完成，尚须向用户交付及实物测试\r\n\r\n'
              '当前112项软件、最终零冲突DRC、非负建立/保持及同源打包和独立CLI校验全部通过。'
              '候选目录：`' + str(destination) + '`。状态和哈希见目录delivery.json、SHA256SUMS.txt；'
              '独立后处理记录build/stage1_completion_20261024_0949/outcome.json。'
              '候选尚未由聊天向Jeremy交付，下一次接续应读取结果并提供bit/ZIP链接，不能静默遗漏交付；'
              '实物验收待测，不推送/上板/Flash。全部旧交付/用户文件保留。\r\n\r\n').encode()
    marker = b'## '; offset = old.index(marker)
    agents.write_bytes(old[:offset] + insert + old[offset:])
    print('G3_CANDIDATE_VERIFIED', destination, flush=True)
except BaseException as error:
    traceback.print_exc()
    if not (O / 'outcome.json').exists():
        save('outcome.json', dict(status='STOPPED_WITHOUT_APPROVED_DELIVERY',
             error=repr(error), time=datetime.datetime.now().isoformat(),
             attempt=ATTEMPT, no_cad_or_simulation_launched=True))
    raise
