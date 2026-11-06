"""Bounded headless boot probe. A response is evidence of life, not fidelity."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time

from diagnostics import ROOT, collect, read_response


def request(port, command, **params):
    with socket.create_connection(('127.0.0.1', port), timeout=3) as sock:
        with sock.makefile('rwb') as stream:
            stream.write((json.dumps(dict(id=100, cmd=command, **params)) + '\n').encode())
            stream.flush()
            return read_response(stream)


def runtime_failures(log_text):
    markers = ('DISPATCH FATAL:', 'FATAL:', 'emulation halted')
    return list(dict.fromkeys(line.strip() for line in log_text.splitlines()
                             if any(marker in line for marker in markers)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=15, choices=range(1, 181))
    parser.add_argument('--opengl', action='store_true')
    parser.add_argument('--host-audio', action='store_true',
                        help='Use a hidden full frontend with the real audio device')
    parser.add_argument('--confirm-after', type=int, default=None,
                        help='Press Cross once after this many seconds (menu probe)')
    parser.add_argument('--confirm-frame', type=int, default=None,
                        help='Wait for a guest frame instead of a wall-time delay')
    parser.add_argument('--button', choices=('cross', 'start', 'circle', 'right', 'left', 'down', 'up'), default='cross')
    parser.add_argument('--sequence', help='Comma-separated buttons; overrides --button and --presses')
    parser.add_argument('--music-file', type=Path, help='Diagnostic build: prepare and insert this MP3')
    parser.add_argument('--music-frame', type=int, default=4100)
    parser.add_argument('--music-on-menu', action='store_true')
    parser.add_argument('--music-demo', action='store_true')
    parser.add_argument('--trace-menu', action='store_true')
    parser.add_argument('--turbo-until-frame', type=int, default=0,
                        help='Accelerate menu traversal only, then restore normal pacing')
    parser.add_argument('--hold-frames', type=int, default=18)
    parser.add_argument('--presses', type=int, choices=range(1, 9), default=1)
    parser.add_argument('--gap-frames', type=int, default=120)
    parser.add_argument('--runtime-dir', type=Path, default=ROOT / 'build-runtime')
    args = parser.parse_args()
    sequence = args.sequence.split(',') if args.sequence else [args.button] * args.presses
    masks = dict(start='0xFFF7', cross='0xBFFF', circle='0xDFFF', right='0xFFDF',
                 left='0xFF7F', down='0xFFBF', up='0xFFEF')
    if not sequence or any(button not in masks for button in sequence):
        parser.error('Invalid button sequence')
    exe = args.runtime_dir.resolve() / 'VibRibbon_Recompiled.exe'
    if not exe.is_file():
        raise SystemExit('Build runtime first')
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    env = dict(os.environ, PSX_DEBUG_SERVER='1')
    env['PSX_OVERLAY_CAPTURES'] = str(reports / 'probe-overlay-captures.json')
    results = dict(mode='hidden-host-audio' if args.host_audio else
                   'headless-opengl' if args.opengl else 'headless',
                   fidelity_verified=False, snapshots=[])
    with (reports / 'smoke-runtime.log').open('w', encoding='utf-8') as log:
        config = ROOT / 'game.local.toml'
        if not config.is_file():
            config = ROOT / 'game.toml'
        process = subprocess.Popen([str(exe), '--game', str(config),
            '--no-launcher', '--hidden-window' if args.host_audio else
            '--headless-opengl' if args.opengl else '--headless',
            '--debug-port', str(port), '--memcard-dir', str(reports / 'smoke-saves')],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic() + args.seconds
            confirm_at = time.monotonic() + args.confirm_after if args.confirm_after is not None else None
            if args.confirm_frame is not None:
                confirm_at = time.monotonic()
            connected = False
            presses_left = len(sequence)
            next_press_frame = args.confirm_frame or 0
            results['input_events'] = []
            music_pending = False
            music_started = False
            turbo_started = False
            turbo_finished = False
            while time.monotonic() < deadline and process.poll() is None:
                try:
                    results['snapshots'].append(request(port, 'frame'))
                    current_frame = results['snapshots'][-1].get('frame', 0)
                    if args.turbo_until_frame and not turbo_started:
                        results['turbo_start'] = request(port, 'turbo', enabled=1)
                        turbo_started = True
                    if turbo_started and not turbo_finished and current_frame >= args.turbo_until_frame:
                        results['turbo_stop'] = request(port, 'turbo', enabled=0)
                        turbo_finished = True
                    auto_menu = False
                    if args.music_file and args.music_on_menu and not music_started:
                        menu_status = request(port, 'mod_cmd', name='vib.music', args='status').get('reply', '')
                        auto_menu = 'open=1 scene=3' in menu_status or 'open=1 scene=8' in menu_status
                    if args.music_file and not music_started and (auto_menu or
                            (not args.music_on_menu and current_frame >= args.music_frame)):
                        results['music_open'] = request(port, 'mod_cmd', name='vib.music', args='open')
                        results['music_prepare'] = request(port, 'mod_cmd', name='vib.music',
                            args='prepare ' + str(args.music_file.resolve()))
                        music_pending = music_started = True
                    if music_pending:
                        music_status = request(port, 'mod_cmd', name='vib.music', args='status')
                        results['music_status'] = music_status
                        if 'busy=0 prepared=1' in music_status.get('reply', ''):
                            results['music_menu_capture'] = request(port, 'present_shot',
                                path=str(reports / 'music-menu.png'))
                            capture_seq = results['music_menu_capture'].get('seq', 0)
                            for _ in range(20):
                                time.sleep(0.05)
                                capture_done = request(port, 'present_shot_seq')
                                if capture_done.get('seq', 0) > capture_seq:
                                    results['music_menu_capture_done'] = capture_done
                                    break
                            results['music_insert'] = request(port, 'mod_cmd', name='vib.music',
                                args='demo' if args.music_demo else 'insert')
                            music_pending = False
                    if not connected:
                        results['connect_pad'] = request(port, 'set_input', buttons='0xFFFF', connected=1, pad_type=0)
                        results['trace_arms'] = [request(port, 'fntrace_arm', target=pc)
                            for pc in ('0x800201C4', '0x800202C0', '0x800205FC', '0x800207D0', '0x800206D4')]
                        connected = True
                    frame_ready = results['snapshots'][-1].get('frame', 0) >= next_press_frame
                    if confirm_at is not None and time.monotonic() >= confirm_at and frame_ready and not music_pending:
                        active_button = sequence[len(sequence) - presses_left]
                        buttons = masks[active_button]
                        if args.trace_menu:
                            request(port, 'fn_clear')
                            request(port, 'fn_filter', lo='0x80020000', hi='0x80054000')
                        results['pad_before'] = request(port, 'pad_status')
                        results['pc_probe_arm'] = request(port, 'pc_probe_arm',
                            pcs='0x80029578,0x8002958C,0x800299E4,0x80029A18,0x800202C0', n=128)
                        start_frame = request(port, 'frame').get('frame', 0)
                        results['confirm_button'] = active_button
                        results['confirm'] = request(port, 'set_input', buttons=buttons, connected=1, pad_type=0)
                        held = time.monotonic() + 4
                        requested_hold = 2 if active_button in ('up', 'down', 'left', 'right') else args.hold_frames
                        while time.monotonic() < held:
                            frame = request(port, 'frame').get('frame', start_frame)
                            if frame - start_frame >= requested_hold:
                                break
                            time.sleep(0.05)
                        results['hold_frame_range'] = [start_frame, frame]
                        menu_calls = request(port, 'fn_entry_dump', count=1024) if args.trace_menu else None
                        if active_button in ('up', 'down', 'left', 'right'):
                            results['arrow_early_release'] = request(port, 'set_input', buttons='0xFFFF', connected=1, pad_type=0)
                        results['pad_held'] = request(port, 'pad_status')
                        results['sio_held'] = request(port, 'sio_state')
                        results['sio_trace_held'] = request(port, 'sio_trace', count=60)
                        results['sio_pc_held'] = request(port, 'sio_pc_trace', count=60)
                        results['pc_probe_held'] = request(port, 'pc_probe_dump')
                        results['menu_configuration'] = request(port, 'read_ram', addr='0x800480B8', len=32)
                        results['loaded_image_probe'] = request(port, 'read_ram', addr='0x80019180', len=64)
                        results['input_calls_held'] = request(port, 'fntrace_dump', count=40)
                        results['input_route_calls'] = request(port, 'fntrace_dump', count=80,
                            target_lo='0x800206D4', target_hi='0x80020800')
                        results['default_input_route'] = request(port, 'read_ram', addr='0x8003FDB4', len=48)
                        results['controller_objects'] = request(port, 'read_ram', addr='0x80047FA0', len=8)
                        objects = bytes.fromhex(results['controller_objects'].get('hex', ''))
                        results['controller_object_data'] = []
                        for at in (0, 4):
                            ptr = int.from_bytes(objects[at:at+4], 'little')
                            if 0 < (ptr & 0x1FFFFFFF) < 0x1FFFE0:
                                obj = request(port, 'read_ram', addr=f'0x{ptr:08X}', len=20)
                                container = bytes.fromhex(obj.get('hex', ''))
                                ptr = int.from_bytes(container[:4], 'little')
                                results['controller_object_data'].append(obj)
                                if 0 < (ptr & 0x1FFFFFFF) < 0x1FFFD8:
                                    results['controller_object_data'].append(request(port, 'read_ram', addr=f'0x{ptr:08X}', len=40))
                        results['title_pad_globals'] = request(port, 'read_ram', addr='0x80043060', len=128)
                        title_globals = bytes.fromhex(results['title_pad_globals'].get('hex', ''))
                        if len(title_globals) >= 56:
                            state_ptr = int.from_bytes(title_globals[52:56], 'little')
                            if 0 < (state_ptr & 0x1FFFFFFF) <= 0x1FFE00:
                                state_reply = request(port, 'read_ram', addr=f'0x{state_ptr:08X}', len=480)
                                results['title_pad_state'] = state_reply
                                state = bytes.fromhex(state_reply.get('hex', ''))
                                results['title_pad_buffers'] = []
                                for at in (0x30, 0x120):
                                    ptr = int.from_bytes(state[at:at+4], 'little')
                                    if 0 < (ptr & 0x1FFFFFFF) < 0x1FFFE0:
                                        results['title_pad_buffers'].append(request(port, 'read_ram', addr=f'0x{ptr:08X}', len=32))
                        # OpenBIOS initPad's original stores establish these pointers.
                        results['openbios_pad_globals'] = request(port, 'read_ram', addr='0x0000AEC0', len=64)
                        raw = bytes.fromhex(results['openbios_pad_globals'].get('hex', ''))
                        if len(raw) >= 36:
                            ptr = int.from_bytes(raw[28:32], 'little')
                            results['pad_buffer_address'] = f'0x{ptr:08X}'
                            if 0 < (ptr & 0x1FFFFFFF) < 0x200000:
                                results['pad_buffer_held'] = request(port, 'read_ram', addr=f'0x{ptr:08X}', len=32)
                        results['release'] = request(port, 'set_input', buttons='0xFFFF', connected=1, pad_type=0)
                        release_frame = request(port, 'frame').get('frame', frame)
                        step = len(results['input_events']) + 1
                        step_screen = request(port, 'screenshot_file', path=str(reports / f'probe-step-{step}.png'))
                        scene = request(port, 'mod_cmd', name='vib.music', args='scene')
                        results['input_events'].append(dict(button=active_button,
                            frame_range=results['hold_frame_range'], release=results['release'],
                            menu_calls=menu_calls,
                            native_scene=scene,
                            pc_decisions=results.get('pc_probe_held'),
                            image_probe=results.get('loaded_image_probe'), screenshot=step_screen))
                        presses_left -= 1
                        next_press_frame = release_frame + args.gap_frames
                        confirm_at = time.monotonic() if presses_left else None
                except (OSError, ValueError):
                    pass
                time.sleep(1)
            if process.poll() is None:
                results['diagnostics'] = collect(port)
                results['postmortem'] = {}
                for command in ('get_registers', 'dispatch_tail', 'bioscall_dump', 'irqctx_ring',
                                'thread_trace', 'restore_trace', 'guest_tty_dump', 'menu_host',
                                'disc_list', 'disc_tray_log'):
                    try:
                        results['postmortem'][command] = request(port, command, count=128)
                    except (OSError, ValueError) as error:
                        results['postmortem'][command] = dict(error=str(error))
                results['postmortem']['kernel_globals'] = request(port, 'read_ram', addr='0x100', len=32)
                results['postmortem']['kernel_context'] = request(port, 'read_ram', addr='0x4900', len=256)
                kernel = bytes.fromhex(results['postmortem']['kernel_globals'].get('hex', ''))
                if len(kernel) >= 12:
                    pcb = int.from_bytes(kernel[8:12], 'little')
                    if 0 < pcb < 0x1FFFFC:
                        pcb_reply = request(port, 'read_ram', addr=hex(pcb), len=4)
                        results['postmortem']['pcb'] = pcb_reply
                        tcb = int.from_bytes(bytes.fromhex(pcb_reply.get('hex', '')), 'little') & 0x1FFFFFFF
                        if 0 < tcb < 0x1FFF00:
                            results['postmortem']['tcb'] = request(port, 'read_ram', addr=hex(tcb), len=256)
                results['final_loaded_image_probe'] = request(port, 'read_ram', addr='0x80019180', len=64)
                (reports / 'diagnostics-latest.json').write_text(
                    json.dumps(results['diagnostics'], indent=2) + '\n', encoding='utf-8')
                try:
                    results['screenshot'] = request(port, 'screenshot_file',
                        path=str(reports / 'smoke-screen.png'))
                    results['quit'] = request(port, 'quit')
                except (OSError, ValueError) as error:
                    results['request_error'] = str(error)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    results['forced_stop'] = True
                    process.terminate()
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            results['exit_code'] = process.returncode
    results['runtime_failures'] = runtime_failures(
        (reports / 'smoke-runtime.log').read_text(encoding='utf-8', errors='replace'))
    results['probe_passed'] = (results['exit_code'] == 0 and
                               not results['runtime_failures'] and
                               results.get('diagnostics', {}).get('connection') == 'connected')
    (reports / 'smoke-boot.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(exit_code=results['exit_code'],
                         responses=len(results['snapshots']),
                         diagnostics=results.get('diagnostics', {}).get('connection'),
                         probe_passed=results['probe_passed'],
                         runtime_failures=results['runtime_failures'],
                         fidelity_verified=False)))
    if not results['probe_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
