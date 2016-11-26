#!/usr/bin/python3
import subprocess
import sys, os, time
import argparse

ON_POSIX = 'posix' in sys.builtin_module_names

tval_protocol_order = ('X', 'Y', 'Vx', 'Vy', 'ANGLE', 'NCPID', 'SHIELD', 'BOOST')
tval_output_order = (4, 2, 3, 0, 1, 5, 6, 7)
max_value_len = max(len(x) for x in tval_protocol_order)

def test_binary(fn): # adapted from http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    fpath, fname = os.path.split(fn)
    if fpath:
        if not os.path.isfile(fn):
            raise argparse.ArgumentTypeError('Binary not found')
        if not os.access(fn, os.X_OK):
            raise argparse.ArgumentTypeError('File not executable')
    else:
        raise argparse.ArgumentTypeError('Binaries have to be specified with path')
    return fn

parser = argparse.ArgumentParser(description="Test CSB simulator implementation.")
parser.add_argument('--binary', 
        default='./simulator_test', 
        type=test_binary,
        help='an executable to call for simulation')
parser.add_argument('--replays', 
        nargs='+', 
        type=argparse.FileType('r'),
        required=True,
        help='replay files to use for generating tests')
parser.add_argument('--gui',action='store_true')
parser.add_argument('-v', '--verbose', action='count', default=0)

# more arguments added further down based on test_categories
test_categories = {
        '01_only_moving': (                                     # 1-3: basic functionality
            ('MOVE_ONLY',), 
            (),            
            ('Replay steps containing only movement')),         
        '02_activating_boosters': (
            ('BOOST',), 
            (),
            ('Replay steps containing a boosting pod')),
        '03_boosters_used_up_already': (
            ('BOOST_DEPLETED',), 
            (),
            ('Replay steps containing a pod trying to use boost a second time')),
        '04_activating_shields': (
            ('SHIELD',), 
            (),                                                 # 4-5: shields (but no collisions)
            ('Replay steps containing a shielding pod without collision')),                
        '05_engine_restarting': (
            ('ENGINE_COOLDOWN',), 
            (), 
            ('Replay steps containing a pod waiting to restart the engine')),
        '06_single_high_impact_collision': (
            ('SINGLE_COLLISION', 'ONLY_HIGH_IMPACT'), 
            (),                                         # 6-10: increasingly complex collisions
            ('Replay steps containing a single high impact collision')),
        '07_multiple_high_impact_collisions': (
            ('MULTI_COLLISION', 'ONLY_HIGH_IMPACT'), 
            (),
            ('Replay steps containing multiple high impact collisions')),
        '08_single_low_impact_collision': (
            ('SINGLE_COLLISION', 'HAS_LOW_IMPACT'), 
            (),
            ('Replay steps containing a single low impact collision')),
        '09_single_high_impact_collision_with_active_shields': (
            ('SINGLE_COLLISION', 'ONLY_HIGH_IMPACT', 'SHIELD'), 
            ('ENGINE_COOLDOWN',),
            ('Replay steps containing a single high impact collision involving a shielded pod')),
        '10_single_low_impact_collision_with_active_shields': (
            ('SINGLE_COLLISION', 'HAS_LOW_IMPACT', 'SHIELD'), 
            ('ENGINE_COOLDOWN',),
            ('Replay steps containing a single low impact collision involving a shielded pod')),
        '11_complex_situations': (      # 11: complex situations not fitting in above categories
            (), 
            (),  
            ('Replay steps containing complex situations'))
        }
category_numbers = sorted([int(cat.split('_')[0]) for cat in test_categories])
category_names = sorted(test_categories.keys())
category_maxlen = max(len(x) for x in test_categories)

# Replay reader
def read_replay(replay_file):
    tags = []
    input_data = []
    move_data = []
    output_data = []
    for line in replay_file:  # note that only very specific lines are interpreted
                              # to allow for additional information in later file formats
        if line.startswith('CHECKPOINTS'):
            yield list(map(int,line.split()[1:]))
        elif line.startswith('tags:'):
            tags = line.split()[1:]
        elif line.startswith('IN '):
            input_data.append(line.split()[1:])
        elif line.startswith('MOV '):
            move_data.append(line.split()[1:])
        elif line.startswith('OUT '):
            output_data.append(line.split()[1:])
            if len(output_data) == 4:
                yield tags, input_data, move_data, output_data
                tags = []
                input_data = []
                move_data = []
                output_data = []

class OnlyDisabledList(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        r_list = []
        for cn in category_numbers:
            if cn not in values:
                r_list.append(cn)
        setattr(namespace, self.dest, r_list)

if __name__ == '__main__':
    category_tag_sets = {}
    for cat in category_names:
        mand, opt, help_text = test_categories[cat]
        parser.add_argument('--disable-%s' % cat.split('_')[0], 
                help=help_text,
                dest='disabled',
                action='append_const',
                const=int(cat.split('_')[0]))
        category_tag_sets[cat] = (set(mand), set(mand) | set(opt))
    parser.add_argument('--disabled', 
            nargs='+',
            type=int,
            choices=category_numbers)
    parser.add_argument('--only',
            dest='disabled',
            nargs='+',
            type=int,
            choices=category_numbers,
            action=OnlyDisabledList)

    args = parser.parse_args()
    if args.disabled == None:
        args.disabled = []

    if args.gui:
        import csb_gui
        gui_thread = csb_gui.GUI()
        time.sleep(0.001)  # XXX ugly hack, wait for GUI to initialize

    simulator_pid = subprocess.Popen([args.binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            bufsize=1, universal_newlines=True, close_fds=ON_POSIX)

    test_category_statistics = {tc: [0, 0, 0, 0] for tc in test_categories}

    for replay_file in args.replays:
        fn = replay_file.name

        # count the number of tests first
        replay_reader = read_replay(replay_file)
        next(replay_reader) # skip checkpoints for now
        tests_todo = {}
        filtered_names = [ c  for i, c in enumerate(category_names) if i+1 not in args.disabled ]
        for rnd, (tags, _, _, _) in enumerate(replay_reader):
            for cat in category_names:
                if not (len(category_tag_sets[cat][1]) == 0 or \
                        category_tag_sets[cat][0].issubset(set(tags)) and \
                        set(tags).issubset(category_tag_sets[cat][1])):
                    continue

                # category found, checking whether to execute test
                if cat in filtered_names:
                    tests_todo[rnd] = cat
                break

        replay_file.seek(0)
        replay_reader = read_replay(replay_file)

        cps = next(replay_reader)
        cps = list(zip(*[iter(cps)]*2))
        print(len(cps), file=simulator_pid.stdin)
        for cp in cps:
            print(*cp, file=simulator_pid.stdin)

        if args.gui:
            # read file header
            gui_thread.set_checkpoints(cps)

        print(len(tests_todo), file=simulator_pid.stdin)

        for rnd, (_, input_data, move_data, output_data) in enumerate(replay_reader):
            if rnd in tests_todo:
                for i, in_d in enumerate(input_data):
                    print(*in_d, file=simulator_pid.stdin)
                    #print(*in_d, file=sys.stderr)

                for mo_d in move_data:
                    print(*mo_d, file=simulator_pid.stdin)
                    #print(*mo_d, file=sys.stderr)

                t_data = []
                return_values = []
                for i, ou_d in enumerate(output_data):
                    r_vals = simulator_pid.stdout.readline().split()
                    if len(r_vals) != len(tval_protocol_order):
                        print('ERROR: simulator output has wrong number of values. Expected:', len(tval_protocol_order), 'given:', len(r_vals))
                        exit(-1)
                    return_values.append(r_vals)
                    #print(r_vals, ou_d, file=sys.stderr)
                    t_vals = []
                    for j in range(len(tval_protocol_order)):
                        if tval_protocol_order[j] == 'ANGLE':
                            t_vals.append(abs(round(float(r_vals[j]) - float(ou_d[j]) + 180) % 360 - 180))
                        elif tval_protocol_order[j] == 'NCPID':
                            t_vals.append(min((int(r_vals[j]) - int(ou_d[j])) % len(cps), (int(ou_d[j]) - int(r_vals[j])) % len(cps)))
                        else:
                            t_vals.append(abs(int(r_vals[j]) - int(ou_d[j])))
                    t_data.append(t_vals)
                if args.gui:
                    if any(td_v != 0 for td in t_data[-4:] for td_v in td):
                        print('Round:', rnd)

                        gui_thread.show_position([in_d[:4] + [round(float(in_d[4])),] for in_d in input_data])
                        input() # wait for enter
                        gui_thread.show_position([ou_d[:4] + [round(float(ou_d[4])),] for ou_d in output_data])

                # statistics
                for it in sum(t_data, []): # XXX itertools?
                    if it < 3:
                        test_category_statistics[tests_todo[rnd]][it] += 1
                    else:
                        test_category_statistics[tests_todo[rnd]][3] += 1

                # print data
                table = []
                if args.verbose > 0:
                    for pod, tests in enumerate(t_data):
                        for t_idx in tval_output_order:
                            if tests[t_idx] > 0:
                                table.append((str(pod),
                                        tval_protocol_order[t_idx],
                                        str(tests[t_idx]),
                                        return_values[pod][t_idx],
                                        output_data[pod][t_idx]))
                if len(table) > 0:
                    if args.verbose > 1:
                        print('Test', tests_todo[rnd], 'with data from round', rnd, 'of', fn)
                        columns = len(table[0])
                        c_width = [ max(len(tl[i]) for tl in table) for i in range(columns) ]
                        format_str = 'pod {:>%s}, value {:>%s}: differs by {:>%s}, is: {:>%s}, expected: {:>%s}'
                        format_str = format_str % tuple(c_width)
                        for tl in table:
                            print(format_str.format(*tl))
                        print()
                    elif args.verbose == 1:
                        table_chars = {0:'.', 1:'*', 2:'o', 3:'#'}
                        extra_data = ['test ' + tests_todo[rnd], '', 'round: ' + str(rnd), ' from: ' + fn]
                        for tl, ed in zip(t_data, extra_data):
                            print('  ', end='')
                            for t_val in tl:
                                if t_val < 3:
                                    print(table_chars[t_val], end='')
                                else:
                                    print(table_chars[3], end='')
                            print('   ', ed)
                        print()
                    if args.verbose > 2:
                        print('Full test data:')
                        # angle, vx->nvx vy->nvy x->nx y->ny pncpid cpx cpy
                        dtable = []
                        for i in range(4):
                            od = output_data[i]
                            ind = input_data[i]
                            dtable.append([round(float(od[4]),3), move_data[i][2], ind[2], ind[3], od[2], od[3], ind[0], ind[1], od[0], od[1], ind[5], cps[int(ind[5])][0], cps[int(ind[5])][1]])
                        columns = len(dtable[0])
                        c_width = [ max(len(str(tl[i])) for tl in dtable) for i in range(columns) ]
                        format_str = ' angle {:>%s}, thrust {:>%s}, V ({:>%s}, {:>%s}) -> ({:>%s}, {:>%s}), P ({:>%s}, {:>%s}) -> ({:>%s}, {:>%s}), input ncpid {:>%s} at ({:>%s}, {:>%s})'
                        format_str = format_str % tuple(c_width)
                        for tl in dtable:
                            print(format_str.format(*tl))
                        print()
                           

                if args.gui:
                    if any(td_v != 0 for td in t_data[-4:] for td_v in td):
                        input() # wait for enter
    simulator_pid.kill()

    s_columns = 4
    totals = [sum(test_category_statistics[cat][i] for cat in category_names) for i in range(s_columns)]
    c_width = [ max(len(str(test_category_statistics[cat][i])) for cat in category_names) for i in range(s_columns) ]
    c_width = [ max(c_width[i], len(str(totals[i]))) for i in range(s_columns) ]
    format_str = '{:>%s}:  {:>%s} correct, {:>%s} off-by-1, {:>%s} off-by-2, {:>%s} wrong' % \
            tuple([category_maxlen] + c_width)
    for cat in category_names:
        print(format_str.format(cat, *test_category_statistics[cat]))
    print(format_str.format('TOTAL', *totals))
