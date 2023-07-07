import os

path = "/digi/prod/Projects/FEATURE/EVE_631/shots"

for shot in os.listdir(path):
    lut_dir = os.path.join(path, shot, 'io', 'lut')

    for dirs, folds, files in os.walk(lut_dir):
        for f in files:
            if f.endswith('.cdl'):
                cdl_path = os.path.join(dirs, f)
                cc_path = os.path.join(dirs, f.replace('.cdl', '.cc'))

                if not os.path.exists(cc_path):
                    lines = open(cdl_path).readlines()
                    open(cc_path, 'w').writelines(lines[3:][:-2])
                    print(cc_path)
