"""Rebuild dropped shared units on main, confirm on both runners, review and enqueue.

Private run receipts survive every phase. A comparator failure is terminal for that input;
transport interruptions can resume through the verifier's existing journal. Nothing prunes.
"""
import copy
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import accept_function as af
import check
import flow as f
import flow_lane as lane
import resource_admission

TERMINAL = {'done', 'failed', 'conflict', 'retired', 'stale'}


def relevant(reason):
    return reason.startswith('stale-sibling:') or ('origin changed' in reason and 'carried files' in reason)


def collect(fdir, errors=None):
    """Latest finished selection per address; never consume an in-flight run."""
    chosen, inventories = {}, {}
    files = sorted((Path(fdir) / 'lane/runs').glob('*.json'), key=lambda p: (p.stat().st_mtime_ns, p.name))
    for path in files:
        receipt = lane.read(path)
        if receipt.get('state') not in TERMINAL or lane.owner_alive(receipt.get('owner')):
            continue
        items = {i['id']: i for i in receipt.get('items', [])}
        frozen = Path((receipt.get('candidates') or [''])[0]) / '.local/flow'
        for drop in receipt.get('dropped', []):
            if not relevant(drop.get('reason', '')):
                continue
            request = drop.get('request')
            item = items.get((request or {}).get('item') or drop.get('item'))
            if not item:
                continue
            try:
                source = Path(item['root'])
                if source not in inventories:
                    inventories[source] = f.inventory(source)
                data = inventories[source]
                by_rva = {f.hexrva(fn['rva']): fn for fn in data['functions']}
                if request:
                    functions = request['functions']
                elif item['kind'] == 'family':
                    functions = [f.hexrva(next(fn for fn in data['functions'] if fn['id'] == fid)['rva'])
                                 for fid in f.fr.read(source, item['selection'][0])['population']]
                elif item['kind'] == 'label':
                    functions = item['selection']
                else:
                    names = drop.get('selection') or item['selection']
                    functions = [rv for name in names for rv in f.load_group(frozen, name)['functions']]
                for rva in functions:
                    fn = by_rva[f.hexrva(rva)]
                    record = f.fr.read(source, fn['report'])
                    chosen[fn['build_id'], fn['rva']] = dict(receipt=receipt['id'], root=str(source),
                        function_id=fn['id'], rva=fn['rva'], compiled=record['source']['compiled'],
                        report=fn['report'], reason=drop['reason'], item=item)
            except (OSError, KeyError, ValueError, f.FlowError) as error:
                if errors is not None:
                    errors.append(dict(receipt=receipt['id'], item=item['id'], reason=str(error)))
                continue
    return sorted(chosen.values(), key=lambda d: (d['compiled'], d['rva']))


def merge_bytes(current, base, incoming):
    if current == incoming or incoming == base:
        return current
    if current == base:
        return incoming
    with tempfile.TemporaryDirectory(prefix='reconfirm-merge-') as temporary:
        paths = [Path(temporary) / n for n in ('current', 'base', 'incoming')]
        for path, blob in zip(paths, (current, base, incoming)):
            path.write_bytes(blob)
        result = subprocess.run(['git', 'merge-file', '--quiet', *map(str, paths)], capture_output=True)
        f.refuse(result.returncode == 0, 'unit merge conflict; retained input needs reconciliation')
        return paths[0].read_bytes()


def source_path(root, name):
    f.fr.public_path(name, 'reconstruction/')
    path = (Path(root) / name).resolve()
    f.refuse(path.is_relative_to(Path(root).resolve()) and not (Path(root) / name).is_symlink(),
             'escaping reconstruction input')
    return path


def task_function(fn, record):
    symbol = record['runs'][0]['report']['function'].get('symbol')
    f.refuse(isinstance(symbol, str) and symbol, 'record needs its original verifier task selector')
    result = dict(rva=fn['rva'], size=fn['size'], symbol=symbol)
    if record.get('origin'):
        result['family_metadata'] = {k: record[k] for k in ('origin', 'family_parameters', 'name_source')}
    return result


def link_inputs(root, view):
    shared = Path(f.git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')).parent
    for name in ('sources', 'analysis', 'packs', 'material', 'toolchains'):
        src, dst = shared / '.local' / name, view / '.local' / name
        if src.exists() and not dst.exists():
            dst.symlink_to(src.resolve(), target_is_directory=src.is_dir())
    verifier = view / '.local/verifier'
    verifier.mkdir(exist_ok=True)
    for name in ('runners.json', 'config.json'):
        src = shared / '.local/verifier' / name
        if src.is_file():
            (verifier / name).symlink_to(src.resolve())


def prepare(root, fdir, state):
    run = Path(fdir) / 'reconfirm' / state['id']
    view = run / 'tree'
    f.git(root, 'fetch', '--quiet', 'origin', state['branch'])
    revision = f.git(root, 'rev-parse', 'origin/' + state['branch'])
    f.git(root, 'worktree', 'add', '--quiet', '--detach', str(view), revision)
    (view / '.local/reviews').mkdir(parents=True)
    link_inputs(root, view)
    private = view / '.local/flow'
    lane.snapshot(fdir, private)
    baseline, target = af.load(view)
    by_id = {fn['id']: fn for fn in baseline['functions']}
    state.update(view=str(view), base_revision=revision, held=[], already_matched=[], units={}, targets=[])
    merged_files, prior, carries, inventories, maps = {}, {}, {}, {}, set()
    for drop in state['drops']:
        fid, source = drop['function_id'], Path(drop['root'])
        if fid not in by_id:
            state['held'].append(dict(function_id=fid, reason='inventory entry is not on current origin'))
            continue
        fn = by_id[fid]
        if fn['status'] == 'matched' and not af.acceptance_staleness(fn, view):
            af.validate_match(fn, target, view)
            af.validate_review(fn, f.fr.read(view, fn['report']), view)
            state['already_matched'].append(fid)
            continue
        saved = dict(merged_files)
        try:
            if source not in inventories:
                inventories[source] = {row['id']: row for row in f.inventory(source)['functions']}
            source_fn = inventories[source][fid]
            f.refuse(all(source_fn[key] == fn[key] for key in ('build_id', 'rva', 'size')),
                     'inventory binding changed on main; reconcile explicitly')
            record = af.validate_match(dict(source_fn, status='matched'), target, source)
            base = f.git(source, 'merge-base', 'HEAD', revision)
            for name in record['source']['translation_unit']:
                incoming = source_path(source, name).read_bytes()
                dest = source_path(view, name)
                current = merged_files.get(name, dest.read_bytes() if dest.exists() else b'')
                old = subprocess.run(['git', 'show', base + ':' + name], cwd=source, capture_output=True)
                merged = merge_bytes(current, old.stdout if old.returncode == 0 else b'', incoming)
                merged_files[name] = merged
            copied_fn = copy.deepcopy(source_fn)
            copied_fn['status'] = fn['status']
            copied_fn.pop('named', None)
            carries.setdefault(source, {})[f.hexrva(fn['rva'])] = copied_fn
            if record.get('symbol_map', {}).get('path'):
                maps.add(record['symbol_map']['path'])
            state['targets'].append(fid)
            prior[fid] = str(source)
        except (OSError, ValueError, KeyError, f.FlowError) as error:
            merged_files = saved
            state['held'].append(dict(function_id=fid, reason=str(error)))
    for source, functions in carries.items():
        # Existing harvest equality checks run unchanged; one progress write per input root.
        f.carry_into_tree(source, view, list(functions), functions)
    for name, blob in merged_files.items():
        destination = source_path(view, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(blob)
    for name in maps:
        original = subprocess.run(['git', 'show', revision + ':' + name], cwd=view, capture_output=True)
        if original.returncode == 0:
            (view / name).write_bytes(original.stdout)
    data, _ = af.load(view)
    units = {d['compiled'] for d in state['drops'] if d['function_id'] in state['targets']}
    records = {}
    for fn in data['functions']:
        if fn.get('report') and (view / fn['report']).is_file():
            record = f.fr.read(view, fn['report'])
            records[fn['id']] = record
            if fn['status'] == 'matched' and set(record['source']['translation_unit']) & set(merged_files):
                units.add(record['source']['compiled'])
    # Read each shared report once; only closures touched by these inputs need new builds.
    for fn in data['functions']:
        record = records.get(fn['id'])
        if record is None or record['source']['compiled'] not in units:
            continue
        compiled = record['source']['compiled']
        entry = state['units'].setdefault(compiled, dict(function_ids=[], functions=[], phase='prepared',
                    recipe=record['recipe']['path'], symbols=record['symbol_map']['path']))
        prior_dir = view / '.local/reconfirm/prior'
        prior_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(view / fn['report'], prior_dir / (str(fn['rva']) + '.json'))
        entry['function_ids'].append(fn['id'])
        entry['functions'].append(task_function(fn, record))
    for number, (compiled, unit) in enumerate(sorted(state['units'].items())):
        task = view / '.local/reconfirm/tasks' / f"reconfirm-{state['id']}-{number}"
        task.mkdir(parents=True)
        payload = dict(task_id=task.name, task_schema=1, build_id=target['build_id'], compiled=compiled,
                       recipe=unit['recipe'], symbols=unit['symbols'], functions=unit['functions'])
        lane.write(task / 'task.json', payload)
        unit['task'] = str(task)
    state.update(prior_roots=prior, phase='prepared', build_id=target['build_id'],
                 changed_paths=sorted(merged_files), baseline_functions=baseline['functions'])
    lane.write(run / 'state.json', state)
    return state


def wake_packet(mac):
    raw = bytes.fromhex(mac.replace(':', '').replace('-', ''))
    f.refuse(len(raw) == 6, 'Wake-on-LAN requires a six-byte MAC')
    return b'\xff' * 6 + raw * 16


def runner_preflight(view, wake_mac=None):
    sys.path.insert(0, str(view / 'tools/verifier'))
    import runners
    hosts = runners.for_confirm()
    f.refuse(hosts and len(hosts) >= 2 and all(h['backend'] != 'boat' for h in hosts),
             're-confirmation requires the configured two runner hosts; no Boat fallback')
    for host in hosts:
        if host['backend'] != 'ssh' or host['loader'] != 'native':
            continue
        config = subprocess.run(['ssh', '-G', '-F', host['ssh_config'], host['ssh_host']], capture_output=True, text=True)
        values = dict(line.split(None, 1) for line in config.stdout.splitlines() if len(line.split(None, 1)) == 2)
        f.refuse(config.returncode == 0 and 'hostname' in values, 'cannot resolve the native runner SSH configuration')
        def online():
            try:
                with socket.create_connection((values['hostname'], int(values.get('port', 22))), timeout=3):
                    return True
            except OSError:
                return False
        if online():
            continue
        f.refuse(wake_mac, 'native runner unavailable; configure --wake-mac or restore the host')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(wake_packet(wake_mac), ('255.255.255.255', 9))
        for _ in range(12):
            if online():
                break
            time.sleep(5)
        else:
            raise f.FlowError('native runner unavailable after Wake-on-LAN; no comparator result recorded')
    return hosts


def report_out(view, state, fn, folder='out'):
    return view / '.local/reconfirm' / folder / state['build_id'] / f"0x{fn['rva']:x}.json"


def confirm(state, run, wake_mac=None):
    view = Path(state['view'])
    runner_preflight(view, wake_mac)
    for unit in state['units'].values():
        if unit['phase'] == 'prepared' and comparison_failed(Path(unit['task'])):
            unit.update(phase='held', reason='comparator non-reproduction; never retry into a pass')
    pending = [u for u in state['units'].values() if u['phase'] == 'prepared']
    if pending:
        listing = view / '.local/reconfirm/confirm-list.txt'
        listing.write_text(''.join(u['task'] + '\n' for u in pending))
        state['phase'] = 'confirming'
        lane.write(run / 'state.json', state)
        with (run / 'confirm.log').open('a') as log:
            subprocess.run([sys.executable, str(view / 'tools/verifier/confirm'), '--list', str(listing),
                            '--replace', '--out', str(view / '.local/reconfirm/out')] +
                           (['--allow-low-disk'] if state.get('allow_low_disk') else []), cwd=view,
                           stdout=log, stderr=subprocess.STDOUT)
    data, target = af.load(view)
    by_id = {fn['id']: fn for fn in data['functions']}
    for compiled, unit in state['units'].items():
        if unit['phase'] != 'prepared':
            continue
        try:
            for fid in unit['function_ids']:
                fn = by_id[fid]
                output = report_out(view, state, fn)
                f.refuse(output.is_file(), 'no reproduced record; comparator/transport result remains in confirm.log')
                shutil.copyfile(output, view / fn['report'])
                af.validate_match(dict(fn, status='matched'), target, view)
            unit['phase'] = 'confirmed'
        except (OSError, ValueError, KeyError, af.Refused, f.FlowError) as error:
            unit.update(phase='held', reason=str(error))
    rollback_failed_units(state)
    state['reconfirmed_members'] = sorted(set(state['targets']) &
        {fid for u in state['units'].values() if u['phase'] == 'confirmed' for fid in u['function_ids']})
    lane.write(run / 'state.json', state)



def comparison_failed(task):
    for path in (task / 'confirm').rglob('report.json'):
        result = lane.read(path).get('result')
        if result and result != 'pass':
            return True
    return False


def rollback_failed_units(state):
    """Hold connected changed-file components, preserving all diagnostic outputs."""
    view = Path(state['view'])
    data, _ = af.load(view)
    changed = set(state.get('changed_paths', []))
    closures = {}
    for compiled, unit in state['units'].items():
        paths = set()
        for fid in unit['function_ids']:
            fn = next(row for row in data['functions'] if row['id'] == fid)
            paths.update(f.fr.read(view, fn['report'])['source']['translation_unit'])
        closures[compiled] = paths & changed
    held = {compiled for compiled, unit in state['units'].items() if unit['phase'] == 'held'}
    while True:
        files = set().union(*(closures[name] for name in held)) if held else set()
        expanded = held | {name for name, paths in closures.items() if paths & files}
        if expanded == held:
            break
        held = expanded
    baseline = {fn['id']: fn for fn in state.get('baseline_functions', [])}
    restore = set()
    ids = set()
    for name in held:
        unit = state['units'][name]
        unit.update(phase='held', reason=unit.get('reason', 'shared changed file with a failed unit'))
        ids.update(unit['function_ids']); restore.update(closures[name])
    for fn in data['functions']:
        if fn['id'] in ids:
            restore.add(fn['report'])
    for name in restore:
        result = subprocess.run(['git', 'show', state['base_revision'] + ':' + name], cwd=view, capture_output=True)
        if result.returncode == 0:
            (view / name).write_bytes(result.stdout)
        else:
            (view / name).unlink(missing_ok=True)
    if ids:
        data['functions'] = [baseline.get(fn['id'], fn) if fn['id'] in ids else fn for fn in data['functions']]
        (view / af.PROGRESS).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        state['held'].extend(dict(function_id=fid, reason='re-confirmation failed; unit retained') for fid in sorted(ids))

def copy_group(view, fdir, group, source, prefix):
    copied = dict(group, name=prefix + group['name'], integrated=None)
    path = f.review_path(source, group)
    dest = lane.copy_private_review(source, view, path, group['task_id'] + '.md')
    copied['saved_review'] = dest.relative_to(view).as_posix()
    if group.get('pair'):
        copied['pair'] = prefix + group['pair']
    f.save_group(fdir, copied)
    return copied


def reviews(state, run):
    """Reuse exact full reviews; create fresh Terra groups for new or changed approval bindings."""
    view, private = Path(state['view']), Path(state['view']) / '.local/flow'
    data, _ = af.load(view)
    by_id = {fn['id']: fn for fn in data['functions']}
    good = {fid for u in state['units'].values() if u['phase'] == 'confirmed' for fid in u['function_ids']}
    need = {fid for fid in good if fid in state['targets'] or by_id[fid]['status'] == 'matched'}
    groups, reused, modes = [], set(), {}
    original_groups = f.groups(private)
    for fid in sorted(need):
        fn = by_id[fid]
        record = f.fr.read(view, fn['report'])
        previous = af._json_or_none(view / af.review_record_path(fn))
        if previous and previous.get('source_digest') == record['source']['digest']:
            af.validate_review(fn, record, view)
            continue
        if fn['status'] != 'matched' and fid in state.get('prior_roots', {}):
            source = Path(state['prior_roots'][fid])
            for parent in original_groups.values():
                if parent['kind'] != 'review' or f.hexrva(fn['rva']) not in parent['functions']:
                    continue
                try:
                    status, blocks = f.read_review(source, parent, f.inventory(source)['functions'])
                    if status != 'ok' or blocks.get(f.hexrva(fn['rva']), {}).get('source_digest') != record['source']['digest']:
                        continue
                    prefix = 'reconfirm-' + state['id'] + '-reuse-'
                    copied = copy_group(view, private, parent, source, prefix)
                    if parent.get('pair'):
                        copy_group(view, private, f.load_group(private, parent['pair']), source, prefix)
                    child = f.split_group(view, private, copied['name'], [f.hexrva(fn['rva'])])
                    groups.append(child['name']);reused.add(fid)
                    break
                except (OSError, ValueError, KeyError, af.Refused, f.FlowError):
                    continue
            if fid in reused:
                continue
        old = previous and previous.get('code_section_sha256')
        current = af.record_code_section(record)
        modes[fid] = 'delta' if (previous and previous.get('review_kind') in ('full', 'delta', 'label-only')
                               and old is not None and old == current) else 'full'
    selected = sorted(set(modes), key=lambda fid: by_id[fid]['rva'])
    if selected:
        profile = f.session_profile(private)
        f.refuse(profile == 'claude-low' and af.reviewer_admitted(view, 'gpt-6.1-terra', profile),
                 'fresh Terra review requires the admitted claude-low profile')
        name = 'reconfirm-' + state['id']
        rvas = [f.hexrva(by_id[fid]['rva']) for fid in selected]
        states = {f.hexrva(fn['rva']): {'state': 'accepted' if fn['status'] == 'matched' else 'confirmed',
                                     'profile': profile} for fn in data['functions']}
        components = {rv: f.component_values(view, rv, states[rv], data, 'gpt-6.1-terra') for rv in rvas}
        sample = f.choose_sample(name, rvas, components, f.accepted_counts(view, private, states), state['id'])
        g = dict(name=name, kind='review', task_id='review-' + name, build_id=state['build_id'], functions=rvas,
                 created=f.utc(), source_revision=state['base_revision'], reviewer_model='gpt-6.1-terra', profile=profile,
                 reviewer_harness='codex', components=components, sampled=sample, pair=name+'-s' if sample else None,
                 dispatched=None, rerun=None, integrated=None)
        g['brief'] = f.write_review_brief(view, g, {f.hexrva(fn['rva']): fn for fn in data['functions']})
        f.save_group(private, g);groups.append(name)
        if sample:
            second = f.strong_reviewer_entry(view, profile, 'gpt-6.1-terra')
            strong = dict(g, name=name+'-s', kind='sampling', task_id='review-'+name+'-s', functions=sample,
                          sampled=sample, pair=name, reviewer_model=second['model'], components={})
            strong['brief'] = f.write_review_brief(view, strong, {f.hexrva(fn['rva']): fn for fn in data['functions']})
            f.save_group(private, strong)
    state.update(groups=sorted(set(groups)), review_modes=modes, phase='review_pending')
    # Packet text stays private; it contains reconstructed source and the verified main-history diffs.
    for name in state['groups']:
        g = f.load_group(private, name)
        packet = view / '.local/briefs' / ('packet-' + name + '.md')
        with packet.open('w') as output:
            subprocess.run([sys.executable, str(view/'tools/review_packet.py'), '--template', *g['functions']],
                           cwd=view, stdout=output, stderr=subprocess.DEVNULL, check=True)
        for who in [g] + ([f.load_group(private,g['pair'])] if g.get('pair') else []):
            brief = view / who['brief']
            with brief.open('a') as out:
                out.write('\nRe-confirmation review modes (do not edit source or records):\n')
                out.write(''.join(f'- {f.hexrva(by_id[fid]["rva"])}: {mode}\n' for fid,mode in modes.items()
                                  if f.hexrva(by_id[fid]['rva']) in who['functions']))
                out.write(f'\nPrivate packet: {packet.relative_to(view)}\n')
    lane.write(run / 'state.json', state)


def clean_reruns(state, run):
    view, private = Path(state['view']), Path(state['view'])/'.local/flow'
    data = f.inventory(view);by_rva={f.hexrva(fn['rva']):fn for fn in data['functions']}
    required = {f.unit_of(view,by_rva[rv])[0] for name in state['groups']
                for g in [f.load_group(private,name)] if g.get('sampled') and not g.get('rerun') for rv in g['sampled']}
    if not required:
        return
    for compiled, unit in state['units'].items():
        if compiled in required:
            f.refuse(not comparison_failed(Path(unit['task'])), 'sampling comparator non-reproduction; held')
    listing = view/'.local/reconfirm/rerun-list.txt'
    listing.write_text(''.join(u['task']+'\n' for compiled,u in state['units'].items() if compiled in required))
    with (run/'rerun.log').open('w') as output:
        subprocess.run([sys.executable,str(view/'tools/verifier/confirm'),'--list',str(listing),'--replace',
                        '--out',str(view/'.local/reconfirm/rerun')] +
                       (['--allow-low-disk'] if state.get('allow_low_disk') else []),cwd=view,stdout=output,stderr=subprocess.STDOUT)
    import sampling_packet
    for name in state['groups']:
        g=f.load_group(private,name)
        if not g.get('sampled') or g.get('rerun'):
            continue
        rows=[]
        for rv in g['sampled']:
            fn=by_rva[rv];fresh=report_out(view,state,fn,'rerun')
            f.refuse(fresh.is_file(),'clean sampling re-run has no reproduced record')
            ok,text=sampling_packet.compare(f.fr.read(view,fn['report']),lane.read(fresh))
            rows.append(f'{name} {f.unit_of(view,fn)[0]} {rv} {text}')
            f.refuse(ok,'clean sampling re-run DISAGREE; keep the unit held')
        compare=run/(name+'-compare.txt');compare.write_text('\n'.join(rows)+'\n')
        f.record_rerun(view,private,name,compare)


def enqueue(state, run, fdir):
    view,private=Path(state['view']),Path(state['view'])/'.local/flow'
    data=f.inventory(view);by_id={fn['id']:fn for fn in data['functions']}
    requests=[]
    for name in state['groups']:
        g=f.load_group(private,name);status,blocks=f.read_review(view,g,data['functions'])
        if status=='missing':return False
        f.refuse(status=='ok',status)
        f.refuse(all(blocks.get(rv,{}).get('verdict')=='approve' for rv in g['functions']),
                 're-confirmation review rejected or escalated; unit remains held')
        ok,why=f.sampling_gate(view,private,g,data);f.refuse(ok,str(why))
        requests.append(dict(review=str(f.review_path(view,g)),functions=g['functions'],profile=g['profile']))
    if not requests:
        return False
    af.accept_reviews(view,requests,carry_accepted=True)
    selected={fid for g in state['groups'] for fid,fn in by_id.items() if f.hexrva(fn['rva']) in f.load_group(private,g)['functions']}
    refresh=[fid for u in state['units'].values() if u['phase']=='confirmed' for fid in u['function_ids']
             if fid not in selected and by_id[fid]['status']!='matched']
    shared=Path(fdir).parent.parent
    for name in state['groups']:
        group=f.load_group(private,name);group['record_refresh']=refresh
        for g in [group]+([f.load_group(private,group['pair'])] if group.get('pair') else []):
            source=f.review_path(view,g)
            if source.is_file():
                dest=lane.copy_private_review(view,shared,source,g['task_id']+'.md')
                g['saved_review']=dest.relative_to(shared).as_posix()
            f.save_group(fdir,g)
        f.save_group(private,group)
        lane.enqueue(view,fdir,'review',[name],name='reconfirm-'+state['id'])
    state.update(phase='queued',requeued_members=sorted(set(state['targets'])&selected))
    lane.write(run/'state.json',state)
    return True


def execute(root,fdir,*,resume=None,dry_run=False,wake_mac=None,allow_low_disk=False):
    root,fdir=Path(root).resolve(),Path(fdir).resolve()
    if resume:
        f.refuse(Path(resume).name==resume and resume not in ('.','..'),'invalid re-confirmation run id')
        run=fdir/'reconfirm'/resume;state=lane.read(run/'state.json')
    else:
        errors=[]
        drops=collect(fdir,errors)
        if dry_run:return dict(phase='dry_run',dropped_members=len(drops),unavailable_inputs=errors,units=sorted({d['compiled'] for d in drops}))
        resource_admission.admit(root,'re-confirm dropped units',allow_low_disk=allow_low_disk)
        state=dict(reconfirm_schema=1,id=uuid.uuid4().hex[:12],branch='main',drops=drops,phase='new',unavailable_inputs=errors)
        state['allow_low_disk']=allow_low_disk
        run=fdir/'reconfirm'/state['id'];run.mkdir(parents=True)
        lane.write(run/'state.json',state)
    with (run/'.lock').open('a') as handle:
        import fcntl
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise f.FlowError('this re-confirmation run already has an owner') from None
        if state['phase']=='new':prepare(root,fdir,state)
        if state['phase'] in ('prepared','confirming'):
            confirm(state,run,wake_mac)
            reviews(state,run)
            clean_reruns(state,run)
        if state['phase']=='review_pending':
            clean_reruns(state,run)
            enqueue(state,run,fdir)
        return dict(run=state['id'],phase=state['phase'],view=state['view'],
                    reconfirmed=len(state.get('reconfirmed_members',[])),requeued=len(state.get('requeued_members',[])),
                    held=state.get('held',[]),unavailable_inputs=state.get('unavailable_inputs',[]),groups=state.get('groups',[]),
                    resume_command=f'python3 tools/flow.py reconfirm-dropped --resume {state["id"]}')
